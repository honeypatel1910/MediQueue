from datetime import date, datetime, time
from uuid import uuid4

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from app.extensions import csrf, db
from app.models import (
    AuditLog,
    AvailabilityBlock,
    Appointment,
    AppointmentSlot,
    Notification,
    PatientProfile,
    Prescription,
    ProfessionalRegister,
    Role,
    StaffProfile,
    User,
)
from app.prescriptions.routes import PRESCRIPTION_STANDARD_FEE
from app.services import (
    PENDING_APPROVAL_STATUS,
    approve_extra_appointment,
    book_appointment,
    cancel_appointment,
    generate_slots_for_availability,
    log_action,
    notify_user,
    reject_extra_appointment,
    update_appointment_status,
    validate_staff_availability_window,
)

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


def staff_json(staff):
    """Return staff profile data for admin user management."""
    register = staff.professional_register
    role_name = staff.user.role.name if staff.user and staff.user.role else staff.job_title
    return {
        "id": str(staff.id),
        "name": staff.user.full_name if staff.user else "Clinical staff",
        "role": role_name if role_name in {"Doctor", "Nurse"} else staff.job_title,
        "specialisation": staff.department or staff.job_title or "General Practice",
        "email": staff.user.email if staff.user else "",
        "status": "Verified" if register and register.verified else "Pending",
        "licenceNumber": f"{register.register_name}-{register.registration_number}" if register else "",
        "userId": str(staff.user_id),
    }


def public_user_json(user):
    """Return a safe user record for the admin management table."""
    payload = {
        "id": str(user.id),
        "name": user.full_name,
        "email": user.email,
        "role": role_to_frontend(user.role.name if user.role else "Patient"),
        "status": "Active" if user.active else "Inactive",
        "registered": user.created_at.date().isoformat() if user.created_at else "",
    }
    if user.staff_profile:
        payload.update(staff_json(user.staff_profile))
        payload["userId"] = str(user.id)
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


def availability_block_json(block):
    """Return staff availability and generated slots for the React frontend."""
    appointment_count = (
        Appointment.query.join(AppointmentSlot, Appointment.appointment_slot_id == AppointmentSlot.id)
        .filter(AppointmentSlot.availability_block_id == block.id)
        .count()
    )

    slots = []
    for slot in sorted(block.slots or [], key=lambda item: item.start_at):
        slots.append(
            {
                "id": str(slot.id),
                "startTime": slot.start_at.strftime("%H:%M") if slot.start_at else "",
                "endTime": slot.end_at.strftime("%H:%M") if slot.end_at else "",
                "status": slot.status,
            }
        )

    return {
        "id": str(block.id),
        "date": block.available_date.isoformat() if block.available_date else "",
        "startTime": block.start_time.strftime("%H:%M") if block.start_time else "",
        "endTime": block.end_time.strftime("%H:%M") if block.end_time else "",
        "slotDuration": block.slot_duration_minutes,
        "location": block.location,
        "slotCount": len(slots),
        "canEdit": appointment_count == 0,
        "slots": slots,
    }


def available_slot_json(slot):
    """Return a bookable appointment slot for the React frontend."""
    staff = slot.staff_profile
    staff_user = staff.user if staff else None
    staff_role = staff_user.role.name if staff_user and staff_user.role else "Doctor"
    duration = 0
    if slot.start_at and slot.end_at:
        duration = int((slot.end_at - slot.start_at).total_seconds() // 60)

    return {
        "id": str(slot.id),
        "staffId": str(staff.id) if staff else "",
        "staffName": staff_user.full_name if staff_user else "Clinical staff",
        "date": slot.start_at.date().isoformat() if slot.start_at else "",
        "time": slot.start_at.strftime("%H:%M") if slot.start_at else "",
        "duration": duration,
        "booked": slot.status != "Available",
        "role": staff_role,
        "specialisation": staff.department or staff.job_title if staff else "General Practice",
        "location": slot.availability_block.location if slot.availability_block else "GP Practice",
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


def audit_json(log):
    """Return audit-log data in the format used by the React admin UI."""
    user = log.user
    role_name = user.role.name if user and user.role else "System"
    return {
        "id": str(log.id),
        "action": log.action,
        "user": user.full_name if user else "System",
        "role": role_name,
        "datetime": log.created_at.isoformat() if log.created_at else "",
        "entity": f"{log.entity_type or 'Record'} #{log.entity_id or ''}".strip(),
        "description": log.details or "",
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

@api_bp.get("/staff/dashboard")
@login_required
def staff_dashboard():
    if not current_user.has_role("Doctor", "Nurse"):
        return json_error("Staff access required.", 403)

    staff = current_user.staff_profile
    if staff is None:
        return json_error("Staff profile was not found.", 404)

    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)

    today_appointments = (
        Appointment.query.filter_by(staff_profile_id=staff.id)
        .join(AppointmentSlot, Appointment.appointment_slot_id == AppointmentSlot.id)
        .filter(AppointmentSlot.start_at >= today_start, AppointmentSlot.start_at <= today_end)
        .order_by(AppointmentSlot.start_at.asc())
        .all()
    )

    schedule = (
        Appointment.query.filter_by(staff_profile_id=staff.id)
        .join(AppointmentSlot, Appointment.appointment_slot_id == AppointmentSlot.id)
        .order_by(AppointmentSlot.start_at.asc())
        .limit(20)
        .all()
    )

    prescriptions = []
    if current_user.has_role("Doctor"):
        prescriptions = (
            Prescription.query.filter(Prescription.status.in_(["Requested", "Under Review"]))
            .order_by(Prescription.created_at.asc())
            .limit(20)
            .all()
        )

    return jsonify(
        {
            "ok": True,
            "todayAppointments": [appointment_json(item) for item in today_appointments],
            "schedule": [appointment_json(item) for item in schedule],
            "prescriptions": [prescription_json(item) for item in prescriptions],
        }
    )




def parse_availability_payload(data):
    """Validate availability payload from React staff availability forms."""
    available_date = data.get("date") or data.get("availableDate")
    start_time_value = data.get("startTime")
    end_time_value = data.get("endTime")
    slot_duration = data.get("slotDuration") or data.get("slotDurationMinutes") or 20
    location = (data.get("location") or "GP Practice").strip() or "GP Practice"

    try:
        parsed_date = date.fromisoformat(available_date)
        parsed_start = time.fromisoformat(start_time_value)
        parsed_end = time.fromisoformat(end_time_value)
        parsed_duration = int(slot_duration)
    except (TypeError, ValueError):
        raise ValueError("Please provide a valid date, time and slot duration.")

    if parsed_date < date.today():
        raise ValueError("Availability must be for today or a future date.")

    if parsed_end <= parsed_start:
        raise ValueError("End time must be after start time.")

    if parsed_duration < 5 or parsed_duration > 120:
        raise ValueError("Slot duration must be between 5 and 120 minutes.")

    start_dt = datetime.combine(parsed_date, parsed_start)
    end_dt = datetime.combine(parsed_date, parsed_end)
    if (end_dt - start_dt).total_seconds() // 60 < parsed_duration:
        raise ValueError("Availability window must be at least one slot long.")

    return parsed_date, parsed_start, parsed_end, parsed_duration, location


def availability_has_appointments(block_id):
    """Return True if generated slots are already linked to appointment records."""
    return (
        Appointment.query.join(AppointmentSlot, Appointment.appointment_slot_id == AppointmentSlot.id)
        .filter(AppointmentSlot.availability_block_id == block_id)
        .first()
        is not None
    )


@api_bp.get("/staff/availability")
@login_required
def staff_availability():
    if not current_user.has_role("Doctor", "Nurse"):
        return json_error("Staff access required.", 403)

    staff = current_user.staff_profile
    if staff is None:
        return json_error("Staff profile was not found.", 404)

    blocks = (
        AvailabilityBlock.query.filter_by(staff_profile_id=staff.id)
        .order_by(AvailabilityBlock.available_date.desc(), AvailabilityBlock.start_time.asc())
        .all()
    )

    return jsonify({"ok": True, "availability": [availability_block_json(block) for block in blocks]})


@api_bp.post("/staff/availability")
@login_required
def create_staff_availability():
    if not current_user.has_role("Doctor", "Nurse"):
        return json_error("Staff access required.", 403)

    staff = current_user.staff_profile
    if staff is None:
        return json_error("Staff profile was not found.", 404)

    data = request.get_json(silent=True) or {}
    try:
        available_date, start_time_value, end_time_value, slot_duration, location = parse_availability_payload(data)
        validate_staff_availability_window(
            staff.id,
            available_date,
            start_time_value,
            end_time_value,
        )
    except ValueError as exc:
        return json_error(str(exc), 400)

    block = AvailabilityBlock(
        staff_profile_id=staff.id,
        available_date=available_date,
        start_time=start_time_value,
        end_time=end_time_value,
        slot_duration_minutes=slot_duration,
        location=location,
    )
    db.session.add(block)
    db.session.flush()
    generated = generate_slots_for_availability(block)
    log_action(
        "Availability created",
        "AvailabilityBlock",
        block.id,
        f"{available_date.isoformat()} {start_time_value.strftime('%H:%M')}-{end_time_value.strftime('%H:%M')} generated {len(generated)} slots",
    )
    db.session.commit()

    return jsonify({"ok": True, "availability": availability_block_json(block)}), 201


@api_bp.put("/staff/availability/<int:block_id>")
@login_required
def update_staff_availability(block_id):
    if not current_user.has_role("Doctor", "Nurse"):
        return json_error("Staff access required.", 403)

    staff = current_user.staff_profile
    if staff is None:
        return json_error("Staff profile was not found.", 404)

    block = AvailabilityBlock.query.filter_by(id=block_id, staff_profile_id=staff.id).first()
    if block is None:
        return json_error("Availability was not found.", 404)

    if availability_has_appointments(block.id):
        return json_error("Availability linked to appointments cannot be edited.", 409)

    data = request.get_json(silent=True) or {}
    try:
        available_date, start_time_value, end_time_value, slot_duration, location = parse_availability_payload(data)
        validate_staff_availability_window(
            staff.id,
            available_date,
            start_time_value,
            end_time_value,
            exclude_block_id=block.id,
        )
    except ValueError as exc:
        return json_error(str(exc), 400)

    block.available_date = available_date
    block.start_time = start_time_value
    block.end_time = end_time_value
    block.slot_duration_minutes = slot_duration
    block.location = location
    generated = generate_slots_for_availability(block)
    log_action(
        "Availability updated",
        "AvailabilityBlock",
        block.id,
        f"{available_date.isoformat()} {start_time_value.strftime('%H:%M')}-{end_time_value.strftime('%H:%M')} regenerated {len(generated)} slots",
    )
    db.session.commit()

    return jsonify({"ok": True, "availability": availability_block_json(block)})


@api_bp.get("/appointments")
@login_required
def appointments():
    """Return appointments for the logged-in patient, staff member, or admin."""
    if current_user.has_role("Patient"):
        profile = current_user.patient_profile
        if profile is None:
            return json_error("Patient profile was not found.", 404)
        items = (
            Appointment.query.filter_by(patient_profile_id=profile.id)
            .join(AppointmentSlot, Appointment.appointment_slot_id == AppointmentSlot.id)
            .order_by(AppointmentSlot.start_at.desc())
            .all()
        )
    elif current_user.has_role("Doctor", "Nurse"):
        staff = current_user.staff_profile
        if staff is None:
            return json_error("Staff profile was not found.", 404)
        items = (
            Appointment.query.filter_by(staff_profile_id=staff.id)
            .join(AppointmentSlot, Appointment.appointment_slot_id == AppointmentSlot.id)
            .order_by(AppointmentSlot.start_at.desc())
            .all()
        )
    elif current_user.has_role("Practice Admin"):
        items = Appointment.query.order_by(Appointment.created_at.desc()).all()
    else:
        return json_error("Access denied.", 403)

    return jsonify({"ok": True, "appointments": [appointment_json(item) for item in items]})


@api_bp.post("/appointments/<int:appointment_id>/cancel")
@login_required
def cancel_existing_appointment(appointment_id):
    """Cancel an appointment from the React patient/staff UI."""
    appointment = Appointment.query.get_or_404(appointment_id)

    allowed = False
    if current_user.has_role("Patient") and appointment.patient_profile.user_id == current_user.id:
        allowed = True
    elif current_user.has_role("Doctor", "Nurse") and appointment.staff_profile.user_id == current_user.id:
        allowed = True
    elif current_user.has_role("Practice Admin"):
        allowed = True

    if not allowed:
        return json_error("You do not have permission to cancel this appointment.", 403)

    try:
        cancel_appointment(appointment)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return json_error(str(exc), 400)

    return jsonify({"ok": True, "appointment": appointment_json(appointment)})


@api_bp.get("/staff/schedule")
@login_required
def staff_schedule():
    """Return the logged-in doctor or nurse appointment schedule."""
    if not current_user.has_role("Doctor", "Nurse"):
        return json_error("Staff access required.", 403)

    staff = current_user.staff_profile
    if staff is None:
        return json_error("Staff profile was not found.", 404)

    items = (
        Appointment.query.filter_by(staff_profile_id=staff.id)
        .join(AppointmentSlot, Appointment.appointment_slot_id == AppointmentSlot.id)
        .order_by(AppointmentSlot.start_at.asc())
        .all()
    )
    return jsonify({"ok": True, "appointments": [appointment_json(item) for item in items]})


@api_bp.post("/staff/appointments/<int:appointment_id>/status")
@login_required
def update_staff_appointment_status(appointment_id):
    """Allow staff to update appointment outcomes from the React schedule page."""
    if not current_user.has_role("Doctor", "Nurse", "Practice Admin"):
        return json_error("Staff or admin access required.", 403)

    appointment = Appointment.query.get_or_404(appointment_id)
    if current_user.has_role("Doctor", "Nurse"):
        staff = current_user.staff_profile
        if staff is None or appointment.staff_profile_id != staff.id:
            return json_error("You can only update your own appointments.", 403)

    data = request.get_json(silent=True) or {}
    status = data.get("status")
    internal_note = (data.get("internalNote") or "").strip()

    try:
        if status == "Cancelled":
            cancel_appointment(appointment)
        else:
            update_appointment_status(appointment, status, internal_note)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return json_error(str(exc), 400)

    return jsonify({"ok": True, "appointment": appointment_json(appointment)})


@api_bp.post("/staff/appointments/<int:appointment_id>/approve-extra")
@login_required
def approve_extra_appointment_from_api(appointment_id):
    """Allow a doctor or nurse to approve a pending extra appointment request."""
    if not current_user.has_role("Doctor", "Nurse"):
        return json_error("Staff access required.", 403)

    staff = current_user.staff_profile
    if staff is None:
        return json_error("Staff profile was not found.", 404)

    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.staff_profile_id != staff.id:
        return json_error("You can only approve requests assigned to you.", 403)

    try:
        approve_extra_appointment(appointment)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return json_error(str(exc), 400)

    return jsonify({"ok": True, "appointment": appointment_json(appointment)})


@api_bp.post("/staff/appointments/<int:appointment_id>/reject-extra")
@login_required
def reject_extra_appointment_from_api(appointment_id):
    """Allow a doctor or nurse to reject a pending extra appointment request."""
    if not current_user.has_role("Doctor", "Nurse"):
        return json_error("Staff access required.", 403)

    staff = current_user.staff_profile
    if staff is None:
        return json_error("Staff profile was not found.", 404)

    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.staff_profile_id != staff.id:
        return json_error("You can only reject requests assigned to you.", 403)

    data = request.get_json(silent=True) or {}
    internal_note = (data.get("internalNote") or "").strip()

    try:
        reject_extra_appointment(appointment, internal_note=internal_note)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return json_error(str(exc), 400)

    return jsonify({"ok": True, "appointment": appointment_json(appointment)})


@api_bp.get("/appointments/available")
@login_required
def available_appointments():
    if not current_user.has_role("Patient"):
        return json_error("Patient access required.", 403)

    query = (
        AppointmentSlot.query.join(AvailabilityBlock, AppointmentSlot.availability_block_id == AvailabilityBlock.id)
        .filter(AppointmentSlot.status == "Available")
        .filter(AppointmentSlot.start_at > datetime.now())
    )

    date_filter = (request.args.get("date") or "").strip()
    if date_filter:
        try:
            selected_date = date.fromisoformat(date_filter)
        except ValueError:
            return json_error("Please provide a valid appointment date.", 400)
        query = query.filter(
            AppointmentSlot.start_at >= datetime.combine(selected_date, time.min),
            AppointmentSlot.start_at <= datetime.combine(selected_date, time.max),
        )

    staff_id = (request.args.get("staffId") or "").strip()
    if staff_id:
        try:
            query = query.filter(AvailabilityBlock.staff_profile_id == int(staff_id))
        except ValueError:
            return json_error("Please provide a valid staff member.", 400)

    role_filter = (request.args.get("role") or "").strip().lower()

    slots = query.order_by(AppointmentSlot.start_at.asc()).limit(100).all()
    slot_payload = [available_slot_json(slot) for slot in slots]
    if role_filter in {"doctor", "nurse"}:
        slot_payload = [slot for slot in slot_payload if slot.get("role", "").lower() == role_filter]

    staff_options = {}
    for slot in slot_payload:
        staff_options[slot["staffId"]] = {
            "id": slot["staffId"],
            "name": slot["staffName"],
            "role": slot.get("role", "Doctor"),
            "specialisation": slot.get("specialisation", "General Practice"),
        }

    return jsonify({"ok": True, "slots": slot_payload, "staff": list(staff_options.values())})


@api_bp.post("/appointments/book")
@login_required
def book_available_appointment():
    if not current_user.has_role("Patient"):
        return json_error("Patient access required.", 403)

    profile = current_user.patient_profile
    if profile is None:
        return json_error("Patient profile was not found.", 404)

    data = request.get_json(silent=True) or {}
    slot_id = data.get("slotId") or data.get("slot_id")
    reason = (data.get("reason") or "").strip()

    if not slot_id:
        return json_error("Please choose an appointment slot.", 400)

    try:
        appointment = book_appointment(profile, int(slot_id), reason=reason)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return json_error(str(exc), 400)

    message = "Appointment booked successfully."
    if appointment.status == PENDING_APPROVAL_STATUS:
        message = (
            "You already have 3 active upcoming appointments with this clinician. "
            "This extra appointment request has been sent for approval."
        )

    return jsonify({"ok": True, "appointment": appointment_json(appointment), "message": message})


@api_bp.get("/prescriptions")
@login_required
def list_prescriptions_from_api():
    """Return prescriptions for the current role.

    Patients see their own requests. Doctors see the review queue used by the
    React prescription review page.
    """
    if current_user.has_role("Patient"):
        profile = current_user.patient_profile
        if profile is None:
            return json_error("Patient profile was not found.", 404)

        prescriptions = (
            Prescription.query.filter_by(patient_profile_id=profile.id)
            .order_by(Prescription.created_at.desc())
            .all()
        )
        return jsonify({"ok": True, "prescriptions": [prescription_json(item) for item in prescriptions]})

    if current_user.has_role("Doctor"):
        prescriptions = (
            Prescription.query.filter(Prescription.status.in_(["Requested", "Under Review", "Approved", "Rejected"]))
            .order_by(Prescription.created_at.desc())
            .all()
        )
        return jsonify({"ok": True, "prescriptions": [prescription_json(item) for item in prescriptions]})

    return json_error("Prescription access required.", 403)


@api_bp.post("/prescriptions/<int:prescription_id>/review")
@login_required
def review_prescription_from_api(prescription_id):
    """Allow doctors to review prescription requests from the React frontend."""
    if not current_user.has_role("Doctor"):
        return json_error("Doctor access required.", 403)

    if current_user.staff_profile is None:
        return json_error("Staff profile was not found.", 404)

    prescription = Prescription.query.get_or_404(prescription_id)
    data = request.get_json(silent=True) or {}
    new_status = (data.get("status") or "").strip()

    allowed_statuses = {"Requested", "Under Review", "Approved", "Rejected"}
    if new_status not in allowed_statuses:
        return json_error("Invalid prescription status for doctor review.", 400)

    prescription.status = new_status
    prescription.reviewed_at = datetime.utcnow()
    prescription.reviewed_by_staff_profile_id = current_user.staff_profile.id

    if new_status == "Approved":
        prescription.payment_status = "Pending"
        prescription.amount_due = PRESCRIPTION_STANDARD_FEE
    elif new_status in {"Requested", "Under Review", "Rejected"}:
        prescription.payment_status = "Not Required"
        prescription.amount_due = 0.0

    notify_user(
        prescription.patient_profile.user_id,
        "Prescription updated",
        f"Your prescription request for {prescription.medicine_name} is now: {prescription.status}.",
    )
    log_action(
        "Prescription reviewed",
        "Prescription",
        prescription.id,
        f"Status set to {prescription.status}",
    )
    db.session.commit()

    return jsonify({"ok": True, "prescription": prescription_json(prescription)})


@api_bp.post("/prescriptions/<int:prescription_id>/pay")
@login_required
def pay_prescription_from_api(prescription_id):
    """Record a simulated patient payment for an approved prescription."""
    if not current_user.has_role("Patient"):
        return json_error("Patient access required.", 403)

    profile = current_user.patient_profile
    if profile is None:
        return json_error("Patient profile was not found.", 404)

    prescription = Prescription.query.get_or_404(prescription_id)
    if prescription.patient_profile_id != profile.id:
        return json_error("You can only pay for your own prescription requests.", 403)

    if prescription.payment_status == "Paid":
        return jsonify({"ok": True, "prescription": prescription_json(prescription)})

    if prescription.payment_status != "Pending" or not prescription.amount_due:
        return json_error("There is no payment due for this prescription.", 400)

    data = request.get_json(silent=True) or {}
    prescription.payment_status = "Paid"
    prescription.payment_method = (data.get("method") or "card").strip() or "card"
    prescription.payment_reference = f"MQPAY-{uuid4().hex[:10].upper()}"
    prescription.paid_at = datetime.utcnow()

    notify_user(
        current_user.id,
        "Prescription payment received",
        f"Payment has been received for {prescription.medicine_name}. Reference: {prescription.payment_reference}.",
    )
    log_action(
        "Prescription payment completed",
        "Prescription",
        prescription.id,
        f"Payment reference: {prescription.payment_reference}",
    )
    db.session.commit()

    return jsonify({"ok": True, "prescription": prescription_json(prescription)})

@api_bp.post("/prescriptions/request")
@login_required
def request_prescription_from_api():
    """Create a patient prescription request from the React frontend."""
    if not current_user.has_role("Patient"):
        return json_error("Patient access required.", 403)

    profile = current_user.patient_profile
    if profile is None:
        return json_error("Patient profile was not found.", 404)

    data = request.get_json(silent=True) or {}
    medicine = (data.get("medicine") or data.get("medicineName") or "").strip()
    quantity = (data.get("quantity") or "").strip()
    reason = (data.get("reason") or "").strip()

    if not medicine or not quantity:
        return json_error("Medicine name and quantity are required.", 400)

    prescription = Prescription(
        patient_profile_id=profile.id,
        medicine_name=medicine,
        quantity=quantity,
        reason=reason,
        status="Requested",
        payment_status="Not Required",
        amount_due=0.0,
    )
    db.session.add(prescription)
    db.session.flush()
    log_action(
        "Prescription requested",
        "Prescription",
        prescription.id,
        f"Medicine: {prescription.medicine_name}",
    )
    db.session.commit()

    return jsonify({"ok": True, "prescription": prescription_json(prescription)}), 201




@api_bp.get("/notifications")
@login_required
def notifications():
    """Return notifications for the logged-in user."""
    items = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify({"ok": True, "notifications": [notification_json(item) for item in items]})


@api_bp.post("/notifications/<int:notification_id>/read")
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read for the logged-in user."""
    item = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    item.is_read = True
    db.session.commit()
    return jsonify(
        {
            "ok": True,
            "notification": notification_json(item),
            "unreadCount": unread_notification_count(current_user.id),
        }
    )



@api_bp.get("/admin/dashboard")
@login_required
def admin_dashboard_from_api():
    """Return practice overview data for the React admin dashboard."""
    if not current_user.has_role("Practice Admin"):
        return json_error("Practice admin access required.", 403)

    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)

    total_users = User.query.count()
    active_users = User.query.filter_by(active=True).count()
    patient_count = User.query.join(Role).filter(Role.name == "Patient").count()
    doctor_count = User.query.join(Role).filter(Role.name == "Doctor").count()
    nurse_count = User.query.join(Role).filter(Role.name == "Nurse").count()

    today_appointments = (
        Appointment.query.join(AppointmentSlot, Appointment.appointment_slot_id == AppointmentSlot.id)
        .filter(AppointmentSlot.start_at >= today_start, AppointmentSlot.start_at <= today_end)
        .count()
    )
    upcoming_appointments = (
        Appointment.query.join(AppointmentSlot, Appointment.appointment_slot_id == AppointmentSlot.id)
        .filter(AppointmentSlot.start_at > datetime.now(), Appointment.status == "Booked")
        .count()
    )
    pending_prescriptions = Prescription.query.filter(Prescription.status.in_(["Requested", "Under Review"])).count()
    approved_prescriptions = Prescription.query.filter_by(status="Approved").count()
    paid_prescriptions = Prescription.query.filter_by(payment_status="Paid").count()

    recent_appointments = (
        Appointment.query.join(AppointmentSlot, Appointment.appointment_slot_id == AppointmentSlot.id)
        .order_by(AppointmentSlot.start_at.desc())
        .limit(6)
        .all()
    )
    recent_prescriptions = Prescription.query.order_by(Prescription.created_at.desc()).limit(6).all()
    recent_audit_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(8).all()

    return jsonify(
        {
            "ok": True,
            "summary": {
                "totalUsers": total_users,
                "activeUsers": active_users,
                "patients": patient_count,
                "doctors": doctor_count,
                "nurses": nurse_count,
                "todayAppointments": today_appointments,
                "upcomingAppointments": upcoming_appointments,
                "pendingPrescriptions": pending_prescriptions,
                "approvedPrescriptions": approved_prescriptions,
                "paidPrescriptions": paid_prescriptions,
            },
            "recentAppointments": [appointment_json(item) for item in recent_appointments],
            "recentPrescriptions": [prescription_json(item) for item in recent_prescriptions],
            "recentAuditLogs": [
                {
                    "id": str(item.id),
                    "action": item.action,
                    "entityType": item.entity_type or "System",
                    "details": item.details or "",
                    "createdAt": item.created_at.isoformat() if item.created_at else "",
                    "userName": item.user.full_name if item.user else "System",
                }
                for item in recent_audit_logs
            ],
        }
    )

@api_bp.get("/admin/users")
@login_required
def admin_users_from_api():
    """Return users grouped for the React admin user-management page."""
    if not current_user.has_role("Practice Admin"):
        return json_error("Practice admin access required.", 403)

    users = User.query.order_by(User.created_at.desc()).all()
    staff_profiles = StaffProfile.query.join(User).order_by(User.created_at.desc()).all()

    return jsonify(
        {
            "ok": True,
            "users": [public_user_json(user) for user in users],
            "patients": [public_user_json(user) for user in users if user.has_role("Patient")],
            "staff": [staff_json(staff) for staff in staff_profiles],
        }
    )


@api_bp.post("/admin/users/create")
@login_required
def admin_create_user_from_api():
    """Create a user account from the React admin page."""
    if not current_user.has_role("Practice Admin"):
        return json_error("Practice admin access required.", 403)

    data = request.get_json(silent=True) or {}
    full_name = (data.get("name") or "").strip()
    email = (data.get("email") or "").lower().strip()
    password = data.get("password") or ""
    role_key = (data.get("role") or "patient").strip().lower()

    if not full_name or not email or not password:
        return json_error("Name, email and password are required.", 400)
    if len(password) < 8:
        return json_error("Password must be at least 8 characters long.", 400)
    if User.query.filter_by(email=email).first():
        return json_error("A user with this email already exists.", 409)

    role_name = {
        "patient": "Patient",
        "doctor": "Doctor",
        "nurse": "Nurse",
        "admin": "Practice Admin",
    }.get(role_key, "Patient")

    role = Role.query.filter_by(name=role_name).first()
    if role is None:
        role = Role(name=role_name)
        db.session.add(role)
        db.session.flush()

    name_parts = full_name.split()
    first_name = name_parts[0]
    last_name = " ".join(name_parts[1:]) or role_name

    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        role=role,
        active=True,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    if role_name == "Patient":
        db.session.add(PatientProfile(user=user, patient_reference=f"MQP-{user.id:05d}"))
    elif role_name in {"Doctor", "Nurse"}:
        department = (data.get("specialisation") or "").strip() or ("General Practice" if role_name == "Doctor" else "Practice Nursing")
        staff = StaffProfile(
            user=user,
            job_title=role_name,
            department=department,
            phone_extension="",
        )
        db.session.add(staff)
        db.session.flush()

        licence = (data.get("licenceNumber") or "").strip()
        if licence:
            register_name = "GMC" if role_name == "Doctor" else "NMC"
            cleaned_number = licence.replace("GMC-", "").replace("NMC-", "").strip()
            db.session.add(
                ProfessionalRegister(
                    staff_profile=staff,
                    register_name=register_name,
                    registration_number=cleaned_number,
                    verified=True,
                )
            )

    log_action("User account created", "User", user.id, f"Role: {role_name}")
    db.session.commit()

    return jsonify({"ok": True, "user": public_user_json(user)}), 201


@api_bp.post("/admin/users/<int:user_id>/toggle")
@login_required
def admin_toggle_user_from_api(user_id):
    """Activate or deactivate a user from the React admin page."""
    if not current_user.has_role("Practice Admin"):
        return json_error("Practice admin access required.", 403)

    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return json_error("You cannot deactivate your own account.", 400)

    user.active = not user.active
    log_action("User status updated", "User", user.id, f"Active: {user.active}")
    db.session.commit()

    return jsonify({"ok": True, "user": public_user_json(user)})




@api_bp.get("/admin/appointments")
@login_required
def admin_appointments_from_api():
    """Return all appointments for the React admin appointment-management page."""
    if not current_user.has_role("Practice Admin"):
        return json_error("Practice admin access required.", 403)

    query = Appointment.query.join(AppointmentSlot, Appointment.appointment_slot_id == AppointmentSlot.id)

    status_filter = (request.args.get("status") or "").strip()
    if status_filter and status_filter != "All":
        query = query.filter(Appointment.status == status_filter)

    appointments = query.order_by(AppointmentSlot.start_at.desc()).limit(250).all()
    return jsonify({"ok": True, "appointments": [appointment_json(item) for item in appointments]})


@api_bp.get("/admin/prescriptions")
@login_required
def admin_prescriptions_from_api():
    """Return all prescriptions for the React admin prescription-management page."""
    if not current_user.has_role("Practice Admin"):
        return json_error("Practice admin access required.", 403)

    prescriptions = Prescription.query.order_by(Prescription.created_at.desc()).limit(250).all()
    return jsonify({"ok": True, "prescriptions": [prescription_json(item) for item in prescriptions]})


@api_bp.post("/admin/prescriptions/<int:prescription_id>/status")
@login_required
def admin_update_prescription_status_from_api(prescription_id):
    """Allow practice admin to manage collection states from the React UI."""
    if not current_user.has_role("Practice Admin"):
        return json_error("Practice admin access required.", 403)

    prescription = Prescription.query.get_or_404(prescription_id)
    data = request.get_json(silent=True) or {}
    new_status = (data.get("status") or "").strip()

    if new_status not in {"Ready for Collection", "Collected"}:
        return json_error("Invalid prescription collection status.", 400)

    if new_status == "Ready for Collection":
        if prescription.status != "Approved" or prescription.payment_status != "Paid":
            return json_error("Only approved and paid prescriptions can be marked ready for collection.", 400)
    elif new_status == "Collected":
        if prescription.status != "Ready for Collection":
            return json_error("Only prescriptions ready for collection can be marked as collected.", 400)

    prescription.status = new_status

    notify_user(
        prescription.patient_profile.user_id,
        "Prescription status updated",
        f"Your prescription request for {prescription.medicine_name} is now: {prescription.status}.",
    )
    log_action(
        "Prescription collection status updated",
        "Prescription",
        prescription.id,
        f"Status set to {prescription.status}",
    )
    db.session.commit()

    return jsonify({"ok": True, "prescription": prescription_json(prescription)})

@api_bp.get("/audit-logs")
@login_required
def audit_logs_from_api():
    """Return audit logs for the React admin audit-log page."""
    if not current_user.has_role("Practice Admin"):
        return json_error("Practice admin access required.", 403)

    items = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(300).all()
    return jsonify({"ok": True, "auditLogs": [audit_json(item) for item in items]})


@api_bp.get("/reports/summary")
@login_required
def reports_summary_from_api():
    """Return reporting summary data for the React admin reports page."""
    if not current_user.has_role("Practice Admin"):
        return json_error("Practice admin access required.", 403)

    total_appointments = Appointment.query.count()
    completed_appointments = Appointment.query.filter_by(status="Completed").count()
    cancelled_appointments = Appointment.query.filter_by(status="Cancelled").count()
    total_prescriptions = Prescription.query.count()
    paid_prescriptions = Prescription.query.filter_by(payment_status="Paid").count()

    return jsonify(
        {
            "ok": True,
            "summary": {
                "appointments": total_appointments,
                "completedAppointments": completed_appointments,
                "cancelledAppointments": cancelled_appointments,
                "prescriptions": total_prescriptions,
                "paidPrescriptions": paid_prescriptions,
            },
        }
    )

