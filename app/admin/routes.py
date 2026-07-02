from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.admin import admin_bp
from app.admin.forms import AdminPrescriptionCollectionForm, AdminUserCreateForm
from app.decorators import role_required
from app.extensions import db
from app.models import (
    Appointment,
    AppointmentSlot,
    AuditLog,
    PatientProfile,
    Prescription,
    ProfessionalRegister,
    Role,
    StaffProfile,
    User,
)
from app.services import log_action, notify_user


@admin_bp.route("/dashboard")
@login_required
@role_required("Practice Admin")
def dashboard():
    total_users = User.query.count()
    total_patients = PatientProfile.query.count()
    total_staff = StaffProfile.query.count()
    active_users = User.query.filter_by(active=True).count()
    total_appointments = Appointment.query.count()
    total_prescriptions = Prescription.query.count()
    pending_prescriptions = Prescription.query.filter(Prescription.status.in_(["Requested", "Under Review"])).count()
    roles = Role.query.order_by(Role.name.asc()).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(8).all()

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_patients=total_patients,
        total_staff=total_staff,
        active_users=active_users,
        total_appointments=total_appointments,
        total_prescriptions=total_prescriptions,
        pending_prescriptions=pending_prescriptions,
        roles=roles,
        recent_users=recent_users,
        recent_logs=recent_logs,
    )


@admin_bp.route("/users")
@login_required
@role_required("Practice Admin")
def users():
    role_filter = request.args.get("role", "").strip()
    query = User.query.join(Role)
    if role_filter:
        query = query.filter(Role.name == role_filter)

    users = query.order_by(User.created_at.desc()).all()
    roles = Role.query.order_by(Role.name.asc()).all()
    return render_template("admin/users.html", users=users, roles=roles, role_filter=role_filter)


@admin_bp.route("/users/create", methods=["GET", "POST"])
@login_required
@role_required("Practice Admin")
def create_user():
    form = AdminUserCreateForm()
    roles = Role.query.order_by(Role.name.asc()).all()
    form.role_id.choices = [(role.id, role.name) for role in roles]

    if form.validate_on_submit():
        role = db.session.get(Role, form.role_id.data)
        if role is None:
            flash("Please choose a valid role.", "danger")
            return render_template("admin/create_user.html", form=form)

        user = User(
            email=form.email.data.lower().strip(),
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            role=role,
            active=form.active.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()

        if role.name == "Patient":
            user.patient_profile = PatientProfile(
                phone=form.phone.data or None,
                address=form.address.data or None,
                patient_reference=f"MQP-{user.id:05d}",
            )

        if role.name in {"Doctor", "Nurse"}:
            user.staff_profile = StaffProfile(
                job_title=form.job_title.data or role.name,
                department=form.department.data or None,
                phone_extension=form.phone_extension.data or None,
            )
            db.session.flush()
            if form.registration_number.data or form.register_name.data:
                user.staff_profile.professional_register = ProfessionalRegister(
                    register_name=form.register_name.data or "Clinical Register",
                    registration_number=form.registration_number.data or "Pending",
                    verified=form.verified.data,
                )

        log_action("User created", "User", user.id, f"Created {role.name} account for {user.email}")
        db.session.commit()
        flash("User account created successfully.", "success")
        return redirect(url_for("admin.users"))

    return render_template("admin/create_user.html", form=form)


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@role_required("Practice Admin")
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "warning")
        return redirect(url_for("admin.users"))

    user.active = not user.active
    status = "activated" if user.active else "deactivated"
    log_action("User status updated", "User", user.id, f"{user.email} {status}")
    db.session.commit()
    flash(f"User account {status}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/appointments")
@login_required
@role_required("Practice Admin")
def appointments():
    status_filter = request.args.get("status", "").strip()
    query = Appointment.query.join(Appointment.slot)
    if status_filter:
        query = query.filter(Appointment.status == status_filter)

    appointments = query.order_by(AppointmentSlot.start_at.desc()).all()
    status_options = ["Booked", "Completed", "Cancelled", "Missed"]
    return render_template(
        "admin/appointments.html",
        appointments=appointments,
        status_options=status_options,
        status_filter=status_filter,
    )


@admin_bp.route("/prescriptions")
@login_required
@role_required("Practice Admin")
def prescriptions():
    status_filter = request.args.get("status", "").strip()
    query = Prescription.query
    if status_filter:
        query = query.filter(Prescription.status == status_filter)

    prescriptions = query.order_by(Prescription.created_at.desc()).all()
    collection_form = AdminPrescriptionCollectionForm()
    status_options = ["Requested", "Under Review", "Approved", "Rejected", "Ready for Collection", "Collected"]
    return render_template(
        "admin/prescriptions.html",
        prescriptions=prescriptions,
        collection_form=collection_form,
        status_options=status_options,
        status_filter=status_filter,
    )


@admin_bp.route("/prescriptions/<int:prescription_id>/collection", methods=["POST"])
@login_required
@role_required("Practice Admin")
def update_prescription_collection(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)
    form = AdminPrescriptionCollectionForm()

    if not form.validate_on_submit():
        flash("Please choose a valid collection status.", "danger")
        return redirect(url_for("admin.prescriptions"))

    new_status = form.status.data

    if prescription.status in {"Rejected", "Requested", "Under Review"}:
        flash("Only approved prescriptions can be prepared for collection.", "warning")
        return redirect(url_for("admin.prescriptions"))

    if prescription.payment_status == "Pending":
        flash("Prescription payment must be completed before collection status is updated.", "warning")
        return redirect(url_for("admin.prescriptions"))

    previous_status = prescription.status
    prescription.status = new_status
    notify_user(
        prescription.patient_profile.user_id,
        "Prescription collection updated",
        f"Your prescription for {prescription.medicine_name} is now: {new_status}.",
    )
    log_action(
        "Prescription collection updated",
        "Prescription",
        prescription.id,
        f"{previous_status} to {new_status}",
    )
    db.session.commit()
    flash("Prescription collection status updated.", "success")
    return redirect(url_for("admin.prescriptions"))


@admin_bp.route("/audit-logs")
@login_required
@role_required("Practice Admin")
def audit_logs():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(300).all()
    return render_template("admin/audit_logs.html", logs=logs)
