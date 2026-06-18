from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.auth.forms import LoginForm, RegistrationForm
from app.extensions import db
from app.models import PatientProfile, Role, User

bp = Blueprint("auth", __name__, url_prefix="/auth")


def _get_or_create_patient_role():
    role = Role.query.filter_by(name="Patient").first()
    if role is None:
        role = Role(name="Patient", description="Patient user who can access patient services.")
        db.session.add(role)
        db.session.commit()
    return role


def _post_login_redirect(user):
    """Send patients to the new patient dashboard; other roles use account page for now."""
    if user.has_role("Patient"):
        return redirect(url_for("patients.dashboard"))
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
            login_user(user, remember=form.remember.data)
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
        db.session.commit()

        flash("Patient account created. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@bp.route("/account")
@login_required
def account():
    return render_template("auth/account.html")
