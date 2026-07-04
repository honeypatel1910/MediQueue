from datetime import date

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from app.extensions import csrf, db
from app.models import Appointment, AppointmentSlot, Notification, PatientProfile, Prescription, Role, User
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


def payment_to_frontend(status):
    """Map backend payment labels to frontend display values."""
    if status == "Not Required":
        return "Not required"
    return status or "Not required"


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
                "specialisation": user.staff_profile.department or user.staff_profile.job_title,
            }
        )

    if user.patient_profile:
        payload["patientReference"] = user.patient_profile.patient_reference

    return payload


def appointment_json(appointment):
    """Return appointment data in the format used by the React frontend."""
    slot = appointment.slot
    staff = appointment.staff_profile
    patient = appointment.patient_profile
    duration = 0
    if slot and slot.start_at and slot.end_at:
        duration = int((slot.end_at - slot.start_at).total_seconds() // 60)

    staff_role = staff.user.role.name if staff and staff.user and staff.user.role else "Doctor"

    return {
        "id": str(appointment.id),
        "patientName": patient.user.full_name if patient and patient.user else "Patient",
        "doctorName": staff.user.full_name if staff and staff.user else "Clinical staff",
        "doctorRole": staff_role,
        "specialisation": staff.department or staff.job_title if staff else "General Practice",
        "date": slot.start_at.date().isoformat() if slot and slot.start_at else "",
        "time": slot.start_at.strftime("%H:%M") if slot and slot.start_at else "",
        "reason": appointment.reason or "",
        "status": appointment.status,
        "duration": duration,
    }


def prescription_json(prescription):
    """Return prescription data in the format used by the React frontend."""
    return {
        "id": str(prescription.id),
        "patientName": prescription.patient_profile.user.full_name if prescription.patient_profile and prescription.patient_profile.user else "Patient",
        "medicine": prescription.medicine_name,
        "quantity": prescription.quantity,
        "reason": prescription.reason or "",
        "requestedDate": prescription.created_at.date().isoformat() if prescription.created_at else "",
        "status": prescription.status,
        "paymentStatus": payment_to_frontend(prescription.payment_status),
        "reviewedBy": prescription.reviewed_by_staff.user.full_name if prescription.reviewed_by_staff and prescription.reviewed_by_staff.user else None,
        "amountDue": float(prescription.amount_due or 0.0),
        "paymentReference": prescription.payment_reference,
    }


def notification_json(notification):
    """Return notification data in the format used by the React frontend."""
    title = (notification.title or "").lower()
    type_name = "appointment_booked"
    if "cancel" in title:
        type_name = "appointment_cancelled"
    elif "payment" in title:
        type_name = "payment_received"
    elif "ready" in title:
        type_name = "prescription_ready"
    elif "prescription" in title:
        type_name = "prescription_approved"

    return {
        "id": str(notification.id),
        "type": type_name,
        "title": notification.title,
        "message": notification.message,
        "timestamp": notification.created_at.isoformat() if notification.created_at else "",
        "read": bool(notification.is_read),
    }


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


@api_bp.get("/patient/dashboard")
@login_required
def patient_dashboard():
    if not current_user.has_role("Patient"):
        return json_error("Patient access required.", 403)

    profile = current_user.patient_profile
    if profile is None:
        return json_error("Patient profile was not found.", 404)

    appointments = (
        Appointment.query.filter_by(patient_profile_id=profile.id)
        .join(AppointmentSlot, Appointment.appointment_slot_id == AppointmentSlot.id)
        .order_by(AppointmentSlot.start_at.desc())
        .limit(20)
        .all()
    )
    prescriptions = (
        Prescription.query.filter_by(patient_profile_id=profile.id)
        .order_by(Prescription.created_at.desc())
        .limit(20)
        .all()
    )
    notifications = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(10)
        .all()
    )

    return jsonify(
        {
            "ok": True,
            "appointments": [appointment_json(item) for item in appointments],
            "prescriptions": [prescription_json(item) for item in prescriptions],
            "notifications": [notification_json(item) for item in notifications],
        }
    )


@api_bp.get("/patient/profile")
@login_required
def get_patient_profile():
    if not current_user.has_role("Patient"):
        return json_error("Patient access required.", 403)

    profile = current_user.patient_profile
    if profile is None:
        return json_error("Patient profile was not found.", 404)

    return jsonify(
        {
            "ok": True,
            "profile": {
                "firstName": current_user.first_name,
                "lastName": current_user.last_name,
                "email": current_user.email,
                "patientReference": profile.patient_reference or "",
                "phone": profile.phone or "",
                "address": profile.address or "",
                "dateOfBirth": profile.date_of_birth.isoformat() if profile.date_of_birth else "",
            },
        }
    )


@api_bp.put("/patient/profile")
@login_required
def update_patient_profile():
    if not current_user.has_role("Patient"):
        return json_error("Patient access required.", 403)

    data = request.get_json(silent=True) or {}
    profile = current_user.patient_profile
    if profile is None:
        return json_error("Patient profile was not found.", 404)

    first_name = (data.get("firstName") or "").strip()
    last_name = (data.get("lastName") or "").strip()
    if not first_name or not last_name:
        return json_error("First name and last name are required.")

    current_user.first_name = first_name
    current_user.last_name = last_name
    profile.phone = (data.get("phone") or "").strip()
    profile.address = (data.get("address") or "").strip()

    dob = data.get("dateOfBirth")
    if dob:
        try:
            profile.date_of_birth = date.fromisoformat(dob)
        except ValueError:
            return json_error("Invalid date of birth.")
    else:
        profile.date_of_birth = None

    log_action("Patient profile updated", "PatientProfile", profile.id, "Patient updated their profile through API")
    db.session.commit()

    return jsonify(
        {
            "ok": True,
            "profile": {
                "firstName": current_user.first_name,
                "lastName": current_user.last_name,
                "email": current_user.email,
                "patientReference": profile.patient_reference or "",
                "phone": profile.phone or "",
                "address": profile.address or "",
                "dateOfBirth": profile.date_of_birth.isoformat() if profile.date_of_birth else "",
            },
        }
    )
