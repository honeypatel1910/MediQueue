from datetime import datetime, timezone
from flask import Response

BOOKED_APPOINTMENT_STATUS = "Booked"
ICALENDAR_PRODID = "-//MediQueue//Appointment Calendar Export//EN"


def _format_ics_datetime(value):
    """Format a naive/local datetime for iCalendar export."""
    if value is None:
        return ""
    return value.strftime("%Y%m%dT%H%M%S")


def _format_ics_utc(value):
    """Format a UTC timestamp for iCalendar DTSTAMP."""
    if value is None:
        value = datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _escape_ics_text(value):
    """Escape text according to iCalendar text value rules."""
    text = str(value or "")
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace("\r", "\\n")
    )


def _fold_ics_line(line):
    """Fold long iCalendar lines to keep exported files standards-friendly."""
    encoded = line.encode("utf-8")
    if len(encoded) <= 73:
        return line

    parts = []
    current = ""
    current_len = 0
    for char in line:
        char_len = len(char.encode("utf-8"))
        limit = 73 if not parts else 72
        if current and current_len + char_len > limit:
            parts.append(current)
            current = " " + char
            current_len = 1 + char_len
        else:
            current += char
            current_len += char_len
    if current:
        parts.append(current)
    return "\r\n".join(parts)


def _join_ics_lines(lines):
    return "\r\n".join(_fold_ics_line(line) for line in lines) + "\r\n"


def appointment_is_calendar_exportable(appointment):
    """Only confirmed/booked appointments should be exported to user calendars."""
    return bool(
        appointment
        and appointment.status == BOOKED_APPOINTMENT_STATUS
        and appointment.slot
        and appointment.slot.start_at
        and appointment.slot.end_at
    )


def appointment_calendar_filename(appointment):
    appointment_id = getattr(appointment, "id", "appointment")
    return f"mediqueue-appointment-{appointment_id}.ics"


def _appointment_summary(appointment, audience="patient"):
    staff_name = appointment.staff_profile.user.full_name if appointment.staff_profile and appointment.staff_profile.user else "Clinical staff"
    patient_name = appointment.patient_profile.user.full_name if appointment.patient_profile and appointment.patient_profile.user else "Patient"
    if audience == "staff":
        return f"MediQueue appointment with {patient_name}"
    return f"MediQueue appointment with {staff_name}"


def _appointment_description(appointment, audience="patient"):
    staff = appointment.staff_profile
    patient = appointment.patient_profile
    staff_name = staff.user.full_name if staff and staff.user else "Clinical staff"
    patient_name = patient.user.full_name if patient and patient.user else "Patient"
    reason = appointment.reason or "Not specified"
    status = appointment.status or "Booked"

    if audience == "staff":
        return (
            f"Patient: {patient_name}\n"
            f"Status: {status}\n"
            f"Reason: {reason}\n"
            "This appointment was booked through MediQueue."
        )

    return (
        f"Clinician: {staff_name}\n"
        f"Status: {status}\n"
        f"Reason: {reason}\n"
        "This appointment was booked through MediQueue."
    )


def appointment_to_ics_event(appointment, audience="patient"):
    """Create one VEVENT block for a MediQueue appointment."""
    slot = appointment.slot
    location = slot.availability_block.location if slot and slot.availability_block else "GP Practice"
    updated_at = appointment.updated_at or appointment.created_at or datetime.utcnow()

    lines = [
        "BEGIN:VEVENT",
        f"UID:mediqueue-appointment-{appointment.id}@mediqueue.local",
        f"DTSTAMP:{_format_ics_utc(datetime.now(timezone.utc))}",
        f"DTSTART:{_format_ics_datetime(slot.start_at)}",
        f"DTEND:{_format_ics_datetime(slot.end_at)}",
        f"SUMMARY:{_escape_ics_text(_appointment_summary(appointment, audience=audience))}",
        f"DESCRIPTION:{_escape_ics_text(_appointment_description(appointment, audience=audience))}",
        f"LOCATION:{_escape_ics_text(location)}",
        f"STATUS:CONFIRMED",
        f"SEQUENCE:{int(updated_at.timestamp()) if hasattr(updated_at, 'timestamp') else 0}",
        "END:VEVENT",
    ]
    return lines


def build_appointment_ics(appointment, audience="patient"):
    """Build a complete .ics calendar file for one appointment."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{ICALENDAR_PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    lines.extend(appointment_to_ics_event(appointment, audience=audience))
    lines.append("END:VCALENDAR")
    return _join_ics_lines(lines)


def build_appointments_ics(appointments, audience="staff"):
    """Build a complete .ics calendar file containing multiple appointments."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{ICALENDAR_PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    for appointment in appointments:
        if appointment_is_calendar_exportable(appointment):
            lines.extend(appointment_to_ics_event(appointment, audience=audience))
    lines.append("END:VCALENDAR")
    return _join_ics_lines(lines)


def appointment_ics_attachment(appointment, audience="patient"):
    """Return an attachment descriptor for email_service.send_email."""
    return {
        "filename": appointment_calendar_filename(appointment),
        "content": build_appointment_ics(appointment, audience=audience),
        "mime_type": "text/calendar",
    }


def ics_download_response(ics_content, filename):
    """Return a Flask download response for an iCalendar file."""
    return Response(
        ics_content,
        mimetype="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
