from datetime import datetime, timedelta

from app.extensions import db
from app.models import AppointmentSlot


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
