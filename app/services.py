from datetime import datetime, timedelta

from flask import request
from flask_login import current_user

from app.extensions import db
from app.models import Appointment, AppointmentSlot, AuditLog, AvailabilityBlock, Notification


ACTIVE_APPOINTMENT_STATUSES = {"Booked"}
FINAL_APPOINTMENT_STATUSES = {"Cancelled", "Completed", "Missed"}


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
    """Return True when an active booked appointment overlaps a proposed availability window."""
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
            "This time range already contains a booked appointment. "
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
    """Return True when the slot already has an active booked appointment."""
    return (
        Appointment.query.filter(Appointment.appointment_slot_id == slot_id)
        .filter(Appointment.status.in_(ACTIVE_APPOINTMENT_STATUSES))
        .first()
        is not None
    )


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
    """Book an available slot while preventing duplicate bookings and patient overlaps."""
    if patient_profile is None:
        raise ValueError("Patient profile was not found.")

    slot = AppointmentSlot.query.get(slot_id)
    if slot is None:
        raise ValueError("Selected appointment slot was not found.")

    if slot.start_at <= datetime.now():
        raise ValueError("Only future appointment slots can be booked.")

    with db.session.no_autoflush:
        if slot.status != "Available" or slot_has_active_booking(slot.id):
            slot.status = "Booked"
            raise ValueError("This appointment slot is already booked.")

        if patient_has_overlapping_appointment(patient_profile.id, slot):
            raise ValueError("You already have an appointment at this time.")

    appointment = Appointment(
        patient_profile_id=patient_profile.id,
        staff_profile_id=slot.staff_profile.id,
        appointment_slot_id=slot.id,
        status="Booked",
        reason=reason,
    )
    slot.status = "Booked"
    db.session.add(appointment)
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
    db.session.flush()
    log_action(
        "Appointment booked",
        "Appointment",
        appointment.id,
        f"Slot {slot.start_at.strftime('%Y-%m-%d %H:%M')} with {slot.staff_profile.user.full_name}",
    )
    db.session.flush()
    return appointment


def cancel_appointment(appointment):
    """Cancel a future booked appointment and release the slot for another patient."""
    if appointment.status != "Booked":
        raise ValueError("Only booked appointments can be cancelled.")

    if appointment.slot.start_at <= datetime.now():
        raise ValueError("Only future appointments can be cancelled.")

    appointment.status = "Cancelled"
    appointment.slot.status = "Available"
    notify_user(
        appointment.patient_profile.user_id,
        "Appointment cancelled",
        f"Your appointment on {appointment.slot.start_at.strftime('%d %b %Y')} at {appointment.slot.start_at.strftime('%H:%M')} was cancelled.",
    )
    notify_user(
        appointment.staff_profile.user_id,
        "Appointment cancelled",
        f"Appointment on {appointment.slot.start_at.strftime('%d %b %Y')} at {appointment.slot.start_at.strftime('%H:%M')} was cancelled.",
    )
    log_action(
        "Appointment cancelled",
        "Appointment",
        appointment.id,
        f"Appointment on {appointment.slot.start_at.strftime('%Y-%m-%d %H:%M')}",
    )
    db.session.flush()
    return appointment


def update_appointment_status(appointment, status, internal_note=""):
    """Update appointment outcome after staff review or consultation."""
    allowed_statuses = {"Booked", "Completed", "Missed"}
    if status not in allowed_statuses:
        raise ValueError("Please choose a valid appointment status.")

    if appointment.status == "Cancelled":
        raise ValueError("Cancelled appointments cannot be updated.")

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
