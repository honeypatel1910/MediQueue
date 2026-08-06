from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.auth.forms import (
    LoginForm,
    PasswordResetConfirmForm,
    PasswordResetRequestForm,
    PasswordResetVerifyForm,
    RegistrationForm,
)
from app.email_verification import (
    email_is_verified,
    issue_password_reset_otp,
    issue_registration_otp,
    reset_password_after_otp,
    verify_password_reset_otp,
)
from app.extensions import db
from app.models import PatientProfile, Role, User
from app.services import log_action

bp = Blueprint("auth", __name__, url_prefix="/auth")


def _get_or_create_patient_role():
    role = Role.query.filter_by(name="Patient").first()
    if role is None:
        role = Role(name="Patient", description="Patient user who can access patient services.")
        db.session.add(role)
        db.session.commit()
    return role


def _post_login_redirect(user):
    """Send users to the dashboard for their role."""
    if user.has_role("Patient"):
        return redirect(url_for("patients.dashboard"))
    if user.has_role("Doctor", "Nurse"):
        return redirect(url_for("staff.dashboard"))
    if user.has_role("Practice Admin"):
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("auth.account"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _post_login_redirect(current_user)

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()

        if user and user.is_active and user.check_password(form.password.data):
            if not email_is_verified(user):
                flash("Please verify your email OTP before signing in.", "warning")
                return redirect(url_for("index"))

            login_user(user, remember=form.remember.data)
            log_action("User login", "User", user.id, "Successful login")
            db.session.commit()
            flash("You are now logged in.", "success")
            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)
            return _post_login_redirect(user)

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return _post_login_redirect(current_user)

    form = RegistrationForm()
    if form.validate_on_submit():
        patient_role = _get_or_create_patient_role()
        user = User(
            email=form.email.data.lower().strip(),
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            role=patient_role,
            active=True,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()
        user.patient_profile = PatientProfile(patient_reference=f"MQP-{user.id:05d}")
        log_action("Patient registration", "User", user.id, "New patient account created", user_id=user.id)
        issue_registration_otp(user)
        db.session.commit()

        flash("Patient account created. Please verify the OTP sent to your registered email before logging in.", "success")
        return redirect(url_for("index"))

    return render_template("auth/register.html", form=form)


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return _post_login_redirect(current_user)

    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        success, message, email_sent, user = issue_password_reset_otp(form.email.data)
        if user:
            log_action("Password reset OTP requested", "User", user.id, "Password reset OTP requested", user_id=user.id)
        db.session.commit()

        flash(message, "info")
        if success:
            return redirect(url_for("auth.verify_password_reset", email=form.email.data.lower().strip()))

    return render_template("auth/forgot_password.html", form=form)


@bp.route("/forgot-password/verify", methods=["GET", "POST"])
def verify_password_reset():
    if current_user.is_authenticated:
        return _post_login_redirect(current_user)

    form = PasswordResetVerifyForm()
    email = request.args.get("email") or ""
    if request.method == "GET" and email:
        form.email.data = email.lower().strip()

    if form.validate_on_submit():
        success, message, user = verify_password_reset_otp(form.email.data, form.otp.data)
        if user:
            log_action("Password reset OTP verified", "User", user.id, "Password reset OTP verified", user_id=user.id)
        db.session.commit()

        if success:
            flash(message, "success")
            return redirect(url_for("auth.reset_password", email=form.email.data.lower().strip()))

        flash(message, "danger")

    return render_template("auth/forgot_password_verify.html", form=form)


@bp.route("/forgot-password/reset", methods=["GET", "POST"])
def reset_password():
    if current_user.is_authenticated:
        return _post_login_redirect(current_user)

    form = PasswordResetConfirmForm()
    email = request.args.get("email") or ""
    if request.method == "GET" and email:
        form.email.data = email.lower().strip()

    if form.validate_on_submit():
        success, message, user = reset_password_after_otp(
            form.email.data,
            form.password.data,
            form.confirm_password.data,
        )
        if user:
            log_action("Password reset completed", "User", user.id, "User reset password after OTP verification", user_id=user.id)
        db.session.commit()

        if success:
            flash(message, "success")
            return redirect(url_for("auth.login"))

        flash(message, "danger")

    return render_template("auth/forgot_password_reset.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    log_action("User logout", "User", current_user.id, "User logged out")
    db.session.commit()
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@bp.route("/account")
@login_required
def account():
    return render_template("auth/account.html")
