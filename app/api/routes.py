from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from app.extensions import csrf, db
from app.models import Notification, PatientProfile, Role, User
from app.services import log_action

api_bp = Blueprint("api", __name__, url_prefix="/api")
csrf.exempt(api_bp)


def role_to_frontend(role_name):
    """Map backend role names to frontend role identifiers."""
    return {
        "Patient": "patient",
        "Doctor": "doctor",
        "Nurse": "nurse",
        "Practice Admin": "admin",
    }.get(role_name, "patient")


def user_json(user):
    """Return a safe JSON representation of the logged-in user."""
    payload = {
        "id": str(user.id),
        "name": user.full_name,
        "email": user.email,
        "role": role_to_frontend(user.role.name if user.role else "Patient"),
        "active": bool(user.active),
    }

    if user.staff_profile:
        payload.update(
            {
                "jobTitle": user.staff_profile.job_title,
                "department": user.staff_profile.department,
                "phoneExtension": user.staff_profile.phone_extension,
            }
        )

    if user.patient_profile:
        payload["patientReference"] = user.patient_profile.patient_reference

    return payload


def json_error(message, status=400):
    return jsonify({"ok": False, "error": message}), status


def unread_notification_count(user_id):
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()


@api_bp.get("/health")
def health():
    return jsonify({"ok": True, "service": "MediQueue API"})


@api_bp.get("/session")
def session():
    if current_user.is_authenticated:
        return jsonify(
            {
                "ok": True,
                "user": user_json(current_user),
                "unreadCount": unread_notification_count(current_user.id),
            }
        )

    return jsonify({"ok": True, "user": None, "unreadCount": 0})


@api_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").lower().strip()
    password = data.get("password") or ""
    remember = bool(data.get("remember", True))

    if not email or not password:
        return json_error("Email and password are required.", 400)

    user = User.query.filter_by(email=email).first()
    if user and user.is_active and user.check_password(password):
        login_user(user, remember=remember)
        log_action("User login", "User", user.id, "Successful API login")
        db.session.commit()
        return jsonify(
            {
                "ok": True,
                "user": user_json(user),
                "unreadCount": unread_notification_count(user.id),
            }
        )

    return json_error("Invalid email/password or inactive account.", 401)


@api_bp.post("/logout")
@login_required
def logout():
    user_id = current_user.id
    log_action("User logout", "User", user_id, "API logout")
    db.session.commit()
    logout_user()
    return jsonify({"ok": True})


@api_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}

    first_name = (data.get("firstName") or data.get("first_name") or "").strip()
    last_name = (data.get("lastName") or data.get("last_name") or "").strip()
    email = (data.get("email") or "").lower().strip()
    password = data.get("password") or ""
    phone = (data.get("phone") or "").strip()
    address = (data.get("address") or "").strip()

    if not first_name or not last_name or not email or not password:
        return json_error("First name, last name, email and password are required.")

    if len(password) < 8:
        return json_error("Password must be at least 8 characters long.")

    if User.query.filter_by(email=email).first():
        return json_error("This email is already registered.")

    patient_role = Role.query.filter_by(name="Patient").first()
    if patient_role is None:
        patient_role = Role(name="Patient", description="Patient user who can access patient services.")
        db.session.add(patient_role)
        db.session.flush()

    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        role=patient_role,
        active=True,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    profile = PatientProfile(
        user=user,
        phone=phone,
        address=address,
        patient_reference=f"MQP-{user.id:05d}",
    )
    db.session.add(profile)
    log_action("Patient registration", "User", user.id, "New patient account created through API", user_id=user.id)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return json_error("This account could not be created. Please check the details and try again.")

    return jsonify({"ok": True, "user": user_json(user)}), 201
