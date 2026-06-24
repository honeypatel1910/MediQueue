from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.decorators import role_required
from app.extensions import db
from app.models import Appointment, PatientProfile
from app.patients import patients_bp
from app.patients.forms import PatientProfileForm


def ensure_patient_profile(user):
    """Create a patient profile for older patient accounts that do not have one yet."""
    if user.patient_profile is None:
        user.patient_profile = PatientProfile(
            patient_reference=f"MQP-{user.id:05d}",
        )
        db.session.commit()
    return user.patient_profile


@patients_bp.route("/dashboard")
@login_required
@role_required("Patient")
def dashboard():
    profile = ensure_patient_profile(current_user)
    upcoming_appointments = (
        Appointment.query.filter_by(patient_profile_id=profile.id, status="Booked")
        .order_by(Appointment.created_at.desc())
        .limit(5)
        .all()
    )
    return render_template(
        "patients/dashboard.html",
        profile=profile,
        upcoming_appointments=upcoming_appointments,
    )


@patients_bp.route("/profile", methods=["GET", "POST"])
@login_required
@role_required("Patient")
def profile():
    profile = ensure_patient_profile(current_user)
    form = PatientProfileForm(obj=profile)

    if form.validate_on_submit():
        profile.phone = form.phone.data
        profile.date_of_birth = form.date_of_birth.data
        profile.address = form.address.data
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("patients.profile"))

    return render_template("patients/profile.html", form=form, profile=profile)
