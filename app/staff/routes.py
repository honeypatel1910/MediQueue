from datetime import date, datetime, time

from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.decorators import role_required
from app.extensions import db
from app.models import Appointment, AppointmentSlot, AvailabilityBlock, Prescription, ProfessionalRegister, StaffProfile
from app.services import generate_slots_for_availability, update_appointment_status
from app.staff import staff_bp
from app.staff.forms import AppointmentStatusForm, AvailabilityForm, StaffProfileForm


def ensure_staff_profile(user):
    """Create a staff profile for doctor/nurse accounts that do not have one yet."""
    if user.staff_profile is None:
        title = "General Practitioner" if user.has_role("Doctor") else "Practice Nurse"
        register = "GMC" if user.has_role("Doctor") else "NMC"
        user.staff_profile = StaffProfile(
            job_title=title,
            department="Clinical Services",
        )
        db.session.flush()
        user.staff_profile.professional_register = ProfessionalRegister(
            register_name=register,
            registration_number="Pending",
            verified=False,
        )
        db.session.commit()
    return user.staff_profile


@staff_bp.route("/dashboard")
@login_required
@role_required("Doctor", "Nurse")
def dashboard():
    profile = ensure_staff_profile(current_user)
    availability_count = AvailabilityBlock.query.filter_by(staff_profile_id=profile.id).count()
    available_slot_count = (
        AppointmentSlot.query.join(AvailabilityBlock)
        .filter(AvailabilityBlock.staff_profile_id == profile.id, AppointmentSlot.status == "Available")
        .count()
    )
    today_appointments = (
        Appointment.query.join(AppointmentSlot, Appointment.appointment_slot_id == AppointmentSlot.id)
        .filter(Appointment.staff_profile_id == profile.id)
        .filter(AppointmentSlot.start_at >= datetime.combine(date.today(), time.min))
        .order_by(AppointmentSlot.start_at.asc())
        .limit(5)
        .all()
    )
    pending_prescription_count = 0
    if current_user.has_role("Doctor"):
        pending_prescription_count = Prescription.query.filter(
            Prescription.status.in_(["Requested", "Under Review"])
        ).count()
    upcoming_blocks = (
        AvailabilityBlock.query.filter_by(staff_profile_id=profile.id)
        .order_by(AvailabilityBlock.available_date.asc(), AvailabilityBlock.start_time.asc())
        .limit(5)
        .all()
    )
    return render_template(
        "staff/dashboard.html",
        profile=profile,
        availability_count=availability_count,
        available_slot_count=available_slot_count,
        today_appointments=today_appointments,
        pending_prescription_count=pending_prescription_count,
        upcoming_blocks=upcoming_blocks,
    )


@staff_bp.route("/profile", methods=["GET", "POST"])
@login_required
@role_required("Doctor", "Nurse")
def profile():
    profile = ensure_staff_profile(current_user)
    form = StaffProfileForm(obj=profile)

    if form.validate_on_submit():
        profile.job_title = form.job_title.data or profile.job_title
        profile.department = form.department.data
        profile.phone_extension = form.phone_extension.data
        db.session.commit()
        flash("Staff profile updated successfully.", "success")
        return redirect(url_for("staff.profile"))

    return render_template("staff/profile.html", form=form, profile=profile)


@staff_bp.route("/availability", methods=["GET", "POST"])
@login_required
@role_required("Doctor", "Nurse")
def availability():
    profile = ensure_staff_profile(current_user)
    form = AvailabilityForm()

    if form.validate_on_submit():
        block = AvailabilityBlock(
            staff_profile=profile,
            available_date=form.available_date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            slot_duration_minutes=form.slot_duration_minutes.data,
            location=form.location.data or "GP Practice",
        )
        db.session.add(block)
        db.session.flush()
        slots = generate_slots_for_availability(block)
        db.session.commit()
        flash(f"Availability created with {len(slots)} appointment slots.", "success")
        return redirect(url_for("staff.availability"))

    blocks = (
        AvailabilityBlock.query.filter_by(staff_profile_id=profile.id)
        .order_by(AvailabilityBlock.available_date.desc(), AvailabilityBlock.start_time.asc())
        .all()
    )
    return render_template("staff/availability.html", form=form, blocks=blocks)


@staff_bp.route("/schedule")
@login_required
@role_required("Doctor", "Nurse")
def schedule():
    profile = ensure_staff_profile(current_user)
    appointments = (
        Appointment.query.join(AppointmentSlot, Appointment.appointment_slot_id == AppointmentSlot.id)
        .filter(Appointment.staff_profile_id == profile.id)
        .order_by(AppointmentSlot.start_at.desc())
        .all()
    )
    return render_template("staff/schedule.html", appointments=appointments)


@staff_bp.route("/appointments/<int:appointment_id>/update", methods=["GET", "POST"])
@login_required
@role_required("Doctor", "Nurse")
def update_appointment(appointment_id):
    profile = ensure_staff_profile(current_user)
    appointment = Appointment.query.get_or_404(appointment_id)

    if appointment.staff_profile_id != profile.id:
        flash("You can only update appointments assigned to you.", "danger")
        return redirect(url_for("staff.schedule"))

    form = AppointmentStatusForm(obj=appointment)
    if form.validate_on_submit():
        try:
            update_appointment_status(
                appointment,
                status=form.status.data,
                internal_note=form.internal_note.data,
            )
            db.session.commit()
            flash("Appointment updated successfully.", "success")
            return redirect(url_for("staff.schedule"))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")

    return render_template("staff/update_appointment.html", form=form, appointment=appointment)
