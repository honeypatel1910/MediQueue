from datetime import datetime, timedelta

from app.extensions import db
from app.models import Appointment, AppointmentSlot


ACTIVE_APPOINTMENT_STATUSES = {"Booked"}


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
    """Return True when the slot already has a booked appointment."""
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
    db.session.flush()
    return appointment
