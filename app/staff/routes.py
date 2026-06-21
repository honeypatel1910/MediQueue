from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.decorators import role_required
from app.extensions import db
from app.models import ProfessionalRegister, StaffProfile
from app.staff import staff_bp
from app.staff.forms import StaffProfileForm


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
    return render_template("staff/dashboard.html", profile=profile)


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
