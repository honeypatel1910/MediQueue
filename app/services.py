from datetime import datetime, timedelta

from flask import request
from flask_login import current_user

from app.extensions import db
from app.models import Appointment, AppointmentSlot, AuditLog, AvailabilityBlock, Notification


STANDARD_APPOINTMENT_LIMIT_PER_STAFF = 3
PENDING_APPROVAL_STATUS = "Pending Approval"
REJECTED_APPOINTMENT_STATUS = "Rejected"
ACTIVE_APPOINTMENT_STATUSES = {"Booked", PENDING_APPROVAL_STATUS}
FINAL_APPOINTMENT_STATUSES = {"Cancelled", "Completed", "Missed", REJECTED_APPOINTMENT_STATUS}


def notify_user(user_id, title, message):
    """Create an in-app notification for one user."""
    notification = Notification(user_id=user_id, title=title, message=message)
    db.session.add(notification)
    return notification


def log_action(action, entity_type=None, entity_id=None, details=None, user_id=None):
    """Record an auditable action without committing the transaction."""
    if user_id is None:
        try:
            if current_user and current_user.is_authenticated:
                user_id = current_user.id
        except RuntimeError:
            user_id = None

    try:
        ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
    except RuntimeError:
        ip_address = None

    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address,
    )
    db.session.add(log)
    return log


def find_overlapping_availability(staff_profile_id, available_date, start_time, end_time, exclude_block_id=None):
    """Return an existing availability block that overlaps the proposed time window."""
    query = AvailabilityBlock.query.filter(
        AvailabilityBlock.staff_profile_id == staff_profile_id,
        AvailabilityBlock.available_date == available_date,
        AvailabilityBlock.start_time < end_time,
        AvailabilityBlock.end_time > start_time,
    )

    if exclude_block_id is not None:
        query = query.filter(AvailabilityBlock.id != exclude_block_id)

    return query.order_by(AvailabilityBlock.start_time.asc()).first()


def active_appointment_overlaps_availability(staff_profile_id, available_date, start_time, end_time, exclude_block_id=None):
    """Return True when an active booked or pending appointment overlaps a proposed availability window."""
    window_start = datetime.combine(available_date, start_time)
    window_end = datetime.combine(available_date, end_time)

    query = (
        Appointment.query.join(AppointmentSlot, Appointment.appointment_slot_id == AppointmentSlot.id)
        .join(AvailabilityBlock, AppointmentSlot.availability_block_id == AvailabilityBlock.id)
        .filter(Appointment.staff_profile_id == staff_profile_id)
        .filter(Appointment.status.in_(ACTIVE_APPOINTMENT_STATUSES))
        .filter(AppointmentSlot.start_at < window_end)
        .filter(AppointmentSlot.end_at > window_start)
    )

    if exclude_block_id is not None:
        query = query.filter(AppointmentSlot.availability_block_id != exclude_block_id)

    return query.first() is not None


def validate_staff_availability_window(staff_profile_id, available_date, start_time, end_time, exclude_block_id=None):
    """Ensure a staff member does not publish overlapping availability."""
    overlapping_block = find_overlapping_availability(
        staff_profile_id,
        available_date,
        start_time,
        end_time,
        exclude_block_id=exclude_block_id,
    )
    if overlapping_block is not None:
        raise ValueError(
            "This availability overlaps with an existing schedule for the same staff member. "
            "Please choose a different date or time range."
        )

    if active_appointment_overlaps_availability(
        staff_profile_id,
        available_date,
        start_time,
        end_time,
        exclude_block_id=exclude_block_id,
    ):
        raise ValueError(
            "This time range already contains a booked or pending approval appointment. "
            "Please choose a different date or time range."
        )


def generate_slots_for_availability(availability_block):
    """Generate bookable appointment slots from a staff availability block."""
    AppointmentSlot.query.filter_by(availability_block_id=availability_block.id).delete()

    start_at = datetime.combine(availability_block.available_date, availability_block.start_time)
    end_at = datetime.combine(availability_block.available_date, availability_block.end_time)
    slot_length = timedelta(minutes=availability_block.slot_duration_minutes)

    generated_slots = []
    cursor = start_at
    while cursor + slot_length <= end_at:
        slot = AppointmentSlot(
            availability_block=availability_block,
            start_at=cursor,
            end_at=cursor + slot_length,
            status="Available",
        )
        db.session.add(slot)
        generated_slots.append(slot)
        cursor += slot_length

    db.session.flush()
    return generated_slots


def slot_has_active_booking(slot_id):
    """Return True when the slot already has an active booked or pending appointment."""
    return (
        Appointment.query.filter(Appointment.appointment_slot_id == slot_id)
        .filter(Appointment.status.in_(ACTIVE_APPOINTMENT_STATUSES))
        .first()
        is not None
    )


def count_active_upcoming_appointments_with_staff(patient_profile_id, staff_profile_id):
    """Count a patient's active future appointments or approval requests with one staff member."""
    return (
        Appointment.query.join(AppointmentSlot, Appointment.appointment_slot_id == AppointmentSlot.id)
        .filter(Appointment.patient_profile_id == patient_profile_id)
        .filter(Appointment.staff_profile_id == staff_profile_id)
        .filter(Appointment.status.in_(ACTIVE_APPOINTMENT_STATUSES))
        .filter(AppointmentSlot.start_at > datetime.now())
        .count()
    )


def patient_requires_extra_appointment_approval(patient_profile_id, staff_profile_id):
    """Return True when a patient already has three active upcoming appointments with this staff member."""
    return count_active_upcoming_appointments_with_staff(
        patient_profile_id,
        staff_profile_id,
    ) >= STANDARD_APPOINTMENT_LIMIT_PER_STAFF


def patient_has_overlapping_appointment(patient_profile_id, slot):
    """Prevent one patient booking two active appointments at the same time."""
    return (
        Appointment.query.join(AppointmentSlot, Appointment.appointment_slot_id == AppointmentSlot.id)
        .filter(Appointment.patient_profile_id == patient_profile_id)
        .filter(Appointment.status.in_(ACTIVE_APPOINTMENT_STATUSES))
        .filter(AppointmentSlot.start_at < slot.end_at)
        .filter(AppointmentSlot.end_at > slot.start_at)
        .first()
        is not None
    )


def book_appointment(patient_profile, slot_id, reason=""):
    """Book an available slot or create an extra-appointment approval request.

    A patient may keep up to three active future appointments with the same
    doctor/nurse. The fourth request is not booked immediately; it is held as
    Pending Approval so the staff member can approve or reject it.
    """
    if patient_profile is None:
        raise ValueError("Patient profile was not found.")

    slot = AppointmentSlot.query.get(slot_id)
    if slot is None:
        raise ValueError("Selected appointment slot was not found.")

    if slot.start_at <= datetime.now():
        raise ValueError("Only future appointment slots can be booked.")

    with db.session.no_autoflush:
        if slot.status != "Available" or slot_has_active_booking(slot.id):
            raise ValueError("This appointment slot is already booked or awaiting approval.")

        if patient_has_overlapping_appointment(patient_profile.id, slot):
            raise ValueError("You already have an appointment or pending request at this time.")

        needs_approval = patient_requires_extra_appointment_approval(
            patient_profile.id,
            slot.staff_profile.id,
        )

    appointment_status = PENDING_APPROVAL_STATUS if needs_approval else "Booked"
    slot_status = PENDING_APPROVAL_STATUS if needs_approval else "Booked"

    appointment = Appointment(
        patient_profile_id=patient_profile.id,
        staff_profile_id=slot.staff_profile.id,
        appointment_slot_id=slot.id,
        status=appointment_status,
        reason=reason,
    )
    slot.status = slot_status
    db.session.add(appointment)
    db.session.flush()

    if needs_approval:
        notify_user(
            patient_profile.user_id,
            "Extra appointment request sent",
            f"Your request for {slot.start_at.strftime('%d %b %Y')} at {slot.start_at.strftime('%H:%M')} was sent to {slot.staff_profile.user.full_name} for approval.",
        )
        notify_user(
            slot.staff_profile.user_id,
            "Extra appointment approval required",
            f"{patient_profile.user.full_name} already has {STANDARD_APPOINTMENT_LIMIT_PER_STAFF} active appointments with you and requested an extra slot on {slot.start_at.strftime('%d %b %Y')} at {slot.start_at.strftime('%H:%M')}.",
        )
        log_action(
            "Extra appointment requested",
            "Appointment",
            appointment.id,
            f"Pending approval for slot {slot.start_at.strftime('%Y-%m-%d %H:%M')} with {slot.staff_profile.user.full_name}",
        )
    else:
        notify_user(
            patient_profile.user_id,
            "Appointment booked",
            f"Your appointment on {slot.start_at.strftime('%d %b %Y')} at {slot.start_at.strftime('%H:%M')} has been booked.",
        )
        notify_user(
            slot.staff_profile.user_id,
            "New appointment booked",
            f"A patient booked an appointment on {slot.start_at.strftime('%d %b %Y')} at {slot.start_at.strftime('%H:%M')}.",
        )
        log_action(
            "Appointment booked",
            "Appointment",
            appointment.id,
            f"Slot {slot.start_at.strftime('%Y-%m-%d %H:%M')} with {slot.staff_profile.user.full_name}",
        )

    db.session.flush()
    return appointment


def cancel_appointment(appointment):
    """Cancel a future booked or pending appointment and release the slot."""
    if appointment.status not in {"Booked", PENDING_APPROVAL_STATUS}:
        raise ValueError("Only booked or pending approval appointments can be cancelled.")

    if appointment.slot.start_at <= datetime.now():
        raise ValueError("Only future appointments can be cancelled.")

    previous_status = appointment.status
    appointment.status = "Cancelled"
    appointment.slot.status = "Available"
    notify_user(
        appointment.patient_profile.user_id,
        "Appointment cancelled",
        f"Your {previous_status.lower()} appointment on {appointment.slot.start_at.strftime('%d %b %Y')} at {appointment.slot.start_at.strftime('%H:%M')} was cancelled.",
    )
    notify_user(
        appointment.staff_profile.user_id,
        "Appointment cancelled",
        f"{previous_status} appointment on {appointment.slot.start_at.strftime('%d %b %Y')} at {appointment.slot.start_at.strftime('%H:%M')} was cancelled.",
    )
    log_action(
        "Appointment cancelled",
        "Appointment",
        appointment.id,
        f"Appointment on {appointment.slot.start_at.strftime('%Y-%m-%d %H:%M')}",
    )
    db.session.flush()
    return appointment


def approve_extra_appointment(appointment):
    """Approve a patient's extra appointment request and convert it to a booked appointment."""
    if appointment.status != PENDING_APPROVAL_STATUS:
        raise ValueError("Only pending approval appointments can be approved.")

    if appointment.slot.start_at <= datetime.now():
        raise ValueError("Only future appointment requests can be approved.")

    appointment.status = "Booked"
    appointment.slot.status = "Booked"
    notify_user(
        appointment.patient_profile.user_id,
        "Extra appointment approved",
        f"Your extra appointment request on {appointment.slot.start_at.strftime('%d %b %Y')} at {appointment.slot.start_at.strftime('%H:%M')} was approved.",
    )
    log_action(
        "Extra appointment approved",
        "Appointment",
        appointment.id,
        f"Approved extra request for {appointment.patient_profile.user.full_name}",
    )
    db.session.flush()
    return appointment


def reject_extra_appointment(appointment, internal_note=""):
    """Reject a patient's extra appointment request and release the held slot."""
    if appointment.status != PENDING_APPROVAL_STATUS:
        raise ValueError("Only pending approval appointments can be rejected.")

    if appointment.slot.start_at <= datetime.now():
        raise ValueError("Only future appointment requests can be rejected.")

    appointment.status = REJECTED_APPOINTMENT_STATUS
    appointment.internal_note = internal_note or None
    appointment.slot.status = "Available"
    notify_user(
        appointment.patient_profile.user_id,
        "Extra appointment rejected",
        f"Your extra appointment request on {appointment.slot.start_at.strftime('%d %b %Y')} at {appointment.slot.start_at.strftime('%H:%M')} was rejected. Please contact the practice if you still need urgent help.",
    )
    log_action(
        "Extra appointment rejected",
        "Appointment",
        appointment.id,
        f"Rejected extra request for {appointment.patient_profile.user.full_name}",
    )
    db.session.flush()
    return appointment


def update_appointment_status(appointment, status, internal_note=""):
    """Update appointment outcome after staff review or consultation."""
    allowed_statuses = {"Booked", "Completed", "Missed"}
    if status not in allowed_statuses:
        raise ValueError("Please choose a valid appointment status.")

    if appointment.status == PENDING_APPROVAL_STATUS:
        raise ValueError("Pending approval appointments must be approved or rejected first.")

    if appointment.status in {"Cancelled", REJECTED_APPOINTMENT_STATUS}:
        raise ValueError("Cancelled or rejected appointments cannot be updated.")

    previous_status = appointment.status
    appointment.status = status
    appointment.internal_note = internal_note or None
    log_action(
        "Appointment status updated",
        "Appointment",
        appointment.id,
        f"{previous_status} to {status}",
    )
    db.session.flush()
    return appointment
