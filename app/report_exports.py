"""Reusable reporting helpers for CSV, PDF and filtered report summaries."""

import csv
from datetime import datetime, time
from io import BytesIO, StringIO
from xml.sax.saxutils import escape

from flask import Response
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models import Appointment, AppointmentSlot, Prescription


DATE_INPUT_FORMAT = "%Y-%m-%d"
DISPLAY_DATE_FORMAT = "%d %b %Y"
DISPLAY_DATETIME_FORMAT = "%d %b %Y %H:%M"


class ReportFilterError(ValueError):
    """Raised when the report date filters are invalid."""


def _parse_date(value, field_name):
    value = (value or "").strip()
    if not value:
        return None

    try:
        return datetime.strptime(value, DATE_INPUT_FORMAT).date()
    except ValueError as exc:
        raise ReportFilterError(f"Please enter a valid {field_name} date in YYYY-MM-DD format.") from exc


def parse_report_filters(args):
    """Return validated start/end date objects from request args."""
    start_date = _parse_date(args.get("start_date"), "start")
    end_date = _parse_date(args.get("end_date"), "end")

    if start_date and end_date and start_date > end_date:
        raise ReportFilterError("The report start date cannot be after the end date.")

    return start_date, end_date


def filter_values(start_date, end_date):
    """Return filter values ready to display or include in URLs."""
    return {
        "start_date": start_date.isoformat() if start_date else "",
        "end_date": end_date.isoformat() if end_date else "",
    }


def report_period_label(start_date=None, end_date=None):
    """Return a human-friendly description of the selected report period."""
    if start_date and end_date:
        return f"{start_date.strftime(DISPLAY_DATE_FORMAT)} to {end_date.strftime(DISPLAY_DATE_FORMAT)}"
    if start_date:
        return f"From {start_date.strftime(DISPLAY_DATE_FORMAT)}"
    if end_date:
        return f"Up to {end_date.strftime(DISPLAY_DATE_FORMAT)}"
    return "All available records"


def format_datetime(value, fmt=DISPLAY_DATETIME_FORMAT):
    if not value:
        return ""
    return value.strftime(fmt)


def csv_response(filename, rows):
    """Create a downloadable CSV response."""
    output = StringIO()
    writer = csv.writer(output)
    writer.writerows(rows)

    response = Response(output.getvalue(), mimetype="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


def appointment_query(start_date=None, end_date=None):
    """Return appointment query filtered by appointment slot date."""
    query = Appointment.query.join(AppointmentSlot, Appointment.appointment_slot_id == AppointmentSlot.id)

    if start_date:
        query = query.filter(AppointmentSlot.start_at >= datetime.combine(start_date, time.min))
    if end_date:
        query = query.filter(AppointmentSlot.start_at <= datetime.combine(end_date, time.max))

    return query


def prescription_query(start_date=None, end_date=None):
    """Return prescription query filtered by request date."""
    query = Prescription.query

    if start_date:
        query = query.filter(Prescription.created_at >= datetime.combine(start_date, time.min))
    if end_date:
        query = query.filter(Prescription.created_at <= datetime.combine(end_date, time.max))

    return query


def appointment_rows(appointments):
    """Return appointment rows shared by CSV and PDF exports."""
    rows = []
    for appointment in appointments:
        slot = appointment.slot
        staff = appointment.staff_profile
        patient = appointment.patient_profile
        rows.append(
            [
                appointment.id,
                format_datetime(slot.start_at, "%Y-%m-%d") if slot else "",
                format_datetime(slot.start_at, "%H:%M") if slot else "",
                format_datetime(slot.end_at, "%H:%M") if slot else "",
                patient.user.full_name if patient and patient.user else "",
                patient.user.email if patient and patient.user else "",
                staff.user.full_name if staff and staff.user else "",
                staff.job_title if staff else "",
                appointment.reason or "",
                appointment.status,
                format_datetime(appointment.created_at),
            ]
        )
    return rows


def prescription_rows(prescriptions):
    """Return prescription rows shared by CSV and PDF exports."""
    rows = []
    for prescription in prescriptions:
        patient = prescription.patient_profile
        reviewer = prescription.reviewed_by_staff.user.full_name if prescription.reviewed_by_staff else ""
        rows.append(
            [
                prescription.id,
                format_datetime(prescription.created_at),
                patient.user.full_name if patient and patient.user else "",
                patient.user.email if patient and patient.user else "",
                prescription.medicine_name,
                prescription.quantity,
                prescription.reason or "",
                prescription.status,
                prescription.payment_status,
                f"{prescription.amount_due:.2f}" if prescription.amount_due else "0.00",
                prescription.payment_reference or "",
                reviewer,
                format_datetime(prescription.reviewed_at),
            ]
        )
    return rows


def build_report_summary(start_date=None, end_date=None):
    """Return filtered report summary data for the React reports page."""
    appointments = appointment_query(start_date, end_date)
    prescriptions = prescription_query(start_date, end_date)

    total_appointments = appointments.count()
    completed_appointments = appointments.filter(Appointment.status == "Completed").count()
    cancelled_appointments = appointments.filter(Appointment.status == "Cancelled").count()
    booked_appointments = appointments.filter(Appointment.status == "Booked").count()
    pending_approval_appointments = appointments.filter(Appointment.status == "Pending Approval").count()
    missed_appointments = appointments.filter(Appointment.status == "Missed").count()
    rejected_appointments = appointments.filter(Appointment.status == "Rejected").count()

    total_prescriptions = prescriptions.count()
    paid_prescriptions = prescriptions.filter(Prescription.payment_status == "Paid").count()
    pending_payment_prescriptions = prescriptions.filter(Prescription.payment_status == "Pending").count()
    requested_prescriptions = prescriptions.filter(Prescription.status == "Requested").count()
    under_review_prescriptions = prescriptions.filter(Prescription.status == "Under Review").count()
    approved_prescriptions = prescriptions.filter(Prescription.status == "Approved").count()
    ready_prescriptions = prescriptions.filter(Prescription.status == "Ready for Collection").count()
    collected_prescriptions = prescriptions.filter(Prescription.status == "Collected").count()
    rejected_prescriptions = prescriptions.filter(Prescription.status == "Rejected").count()

    return {
        "appointments": total_appointments,
        "completedAppointments": completed_appointments,
        "cancelledAppointments": cancelled_appointments,
        "bookedAppointments": booked_appointments,
        "pendingApprovalAppointments": pending_approval_appointments,
        "missedAppointments": missed_appointments,
        "rejectedAppointments": rejected_appointments,
        "prescriptions": total_prescriptions,
        "paidPrescriptions": paid_prescriptions,
        "pendingPaymentPrescriptions": pending_payment_prescriptions,
        "requestedPrescriptions": requested_prescriptions,
        "underReviewPrescriptions": under_review_prescriptions,
        "approvedPrescriptions": approved_prescriptions,
        "readyPrescriptions": ready_prescriptions,
        "collectedPrescriptions": collected_prescriptions,
        "rejectedPrescriptions": rejected_prescriptions,
        "periodLabel": report_period_label(start_date, end_date),
        "filters": filter_values(start_date, end_date),
    }


def _pdf_cell(value, style):
    text = escape(str(value if value is not None else ""))
    return Paragraph(text, style)


def pdf_response(filename, title, subtitle, headers, rows, column_widths=None):
    """Create a landscape PDF report response using ReportLab."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1 * cm,
        leftMargin=1 * cm,
        topMargin=1 * cm,
        bottomMargin=1 * cm,
    )

    base_styles = getSampleStyleSheet()
    title_style = base_styles["Title"]
    subtitle_style = ParagraphStyle(
        "MediQueueReportSubtitle",
        parent=base_styles["BodyText"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#475569"),
        fontSize=9,
        leading=12,
    )
    header_style = ParagraphStyle(
        "MediQueueReportHeader",
        parent=base_styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=8,
        textColor=colors.white,
    )
    cell_style = ParagraphStyle(
        "MediQueueReportCell",
        parent=base_styles["BodyText"],
        fontSize=7,
        leading=8,
        textColor=colors.HexColor("#0f172a"),
    )

    table_data = [[_pdf_cell(header, header_style) for header in headers]]
    if rows:
        table_data.extend([[_pdf_cell(cell, cell_style) for cell in row] for row in rows])
    else:
        table_data.append([_pdf_cell("No records found for the selected filters.", cell_style)] + ["" for _ in headers[1:]])

    table = Table(table_data, repeatRows=1, colWidths=column_widths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    story = [
        Paragraph(escape(title), title_style),
        Paragraph(escape(subtitle), subtitle_style),
        Spacer(1, 0.35 * cm),
        table,
    ]
    doc.build(story)

    pdf_value = buffer.getvalue()
    buffer.close()

    response = Response(pdf_value, mimetype="application/pdf")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response
