from flask import render_template, request
from flask_login import login_required
from reportlab.lib.units import cm

from app.decorators import role_required
from app.models import AppointmentSlot, PatientProfile, Prescription, StaffProfile
from app.report_exports import (
    ReportFilterError,
    appointment_query,
    appointment_rows,
    build_report_summary,
    csv_response,
    filter_values,
    parse_report_filters,
    pdf_response,
    prescription_query,
    prescription_rows,
    report_period_label,
)
from app.reports import reports_bp


APPOINTMENT_CSV_HEADERS = [
    "Appointment ID",
    "Date",
    "Start Time",
    "End Time",
    "Patient Name",
    "Patient Email",
    "Clinical Staff",
    "Staff Role",
    "Reason",
    "Status",
    "Created At",
]

PRESCRIPTION_CSV_HEADERS = [
    "Prescription ID",
    "Requested At",
    "Patient Name",
    "Patient Email",
    "Medicine",
    "Quantity",
    "Reason",
    "Status",
    "Payment Status",
    "Amount Due",
    "Payment Reference",
    "Reviewed By",
    "Reviewed At",
]

APPOINTMENT_PDF_HEADERS = ["ID", "Date", "Time", "Patient", "Clinical Staff", "Role", "Status", "Reason"]
APPOINTMENT_PDF_WIDTHS = [1.1 * cm, 2.0 * cm, 2.2 * cm, 3.0 * cm, 3.0 * cm, 2.0 * cm, 2.3 * cm, 8.5 * cm]

PRESCRIPTION_PDF_HEADERS = ["ID", "Requested", "Patient", "Medicine", "Quantity", "Status", "Payment", "Amount", "Reviewed By"]
PRESCRIPTION_PDF_WIDTHS = [1.1 * cm, 3.0 * cm, 3.1 * cm, 3.3 * cm, 2.2 * cm, 2.6 * cm, 2.2 * cm, 1.8 * cm, 3.6 * cm]


def _current_filters():
    return parse_report_filters(request.args)


def _appointment_export_items(start_date=None, end_date=None):
    return appointment_query(start_date, end_date).order_by(AppointmentSlot.start_at.desc()).all()


def _prescription_export_items(start_date=None, end_date=None):
    return prescription_query(start_date, end_date).order_by(Prescription.created_at.desc()).all()


@reports_bp.route("/")
@login_required
@role_required("Practice Admin")
def index():
    try:
        start_date, end_date = _current_filters()
        filter_error = ""
    except ReportFilterError as exc:
        start_date, end_date = None, None
        filter_error = str(exc)

    summary = build_report_summary(start_date, end_date)
    latest_appointments = _appointment_export_items(start_date, end_date)[:5]
    latest_prescriptions = _prescription_export_items(start_date, end_date)[:5]
    filters = filter_values(start_date, end_date)

    return render_template(
        "admin/reports.html",
        total_patients=PatientProfile.query.count(),
        total_staff=StaffProfile.query.count(),
        total_appointments=summary["appointments"],
        booked_appointments=summary["bookedAppointments"],
        completed_appointments=summary["completedAppointments"],
        cancelled_appointments=summary["cancelledAppointments"],
        pending_approval_appointments=summary["pendingApprovalAppointments"],
        missed_appointments=summary["missedAppointments"],
        total_prescriptions=summary["prescriptions"],
        pending_prescriptions=summary["requestedPrescriptions"] + summary["underReviewPrescriptions"],
        paid_prescriptions=summary["paidPrescriptions"],
        latest_appointments=latest_appointments,
        latest_prescriptions=latest_prescriptions,
        filters=filters,
        filter_error=filter_error,
        period_label=summary["periodLabel"],
    )


@reports_bp.route("/appointments.csv")
@login_required
@role_required("Practice Admin")
def appointments_csv():
    start_date, end_date = _current_filters()
    appointments = _appointment_export_items(start_date, end_date)
    return csv_response("mediqueue_appointments.csv", [APPOINTMENT_CSV_HEADERS] + appointment_rows(appointments))


@reports_bp.route("/appointments.pdf")
@login_required
@role_required("Practice Admin")
def appointments_pdf():
    start_date, end_date = _current_filters()
    appointments = _appointment_export_items(start_date, end_date)
    rows = []
    for row in appointment_rows(appointments):
        rows.append([
            row[0],
            row[1],
            f"{row[2]}-{row[3]}",
            row[4],
            row[6],
            row[7],
            row[9],
            row[8],
        ])

    return pdf_response(
        "mediqueue_appointments.pdf",
        "MediQueue Appointment Report",
        f"Reporting period: {report_period_label(start_date, end_date)}",
        APPOINTMENT_PDF_HEADERS,
        rows,
        APPOINTMENT_PDF_WIDTHS,
    )


@reports_bp.route("/prescriptions.csv")
@login_required
@role_required("Practice Admin")
def prescriptions_csv():
    start_date, end_date = _current_filters()
    prescriptions = _prescription_export_items(start_date, end_date)
    return csv_response("mediqueue_prescriptions.csv", [PRESCRIPTION_CSV_HEADERS] + prescription_rows(prescriptions))


@reports_bp.route("/prescriptions.pdf")
@login_required
@role_required("Practice Admin")
def prescriptions_pdf():
    start_date, end_date = _current_filters()
    prescriptions = _prescription_export_items(start_date, end_date)
    rows = []
    for row in prescription_rows(prescriptions):
        rows.append([
            row[0],
            row[1],
            row[2],
            row[4],
            row[5],
            row[7],
            row[8],
            row[9],
            row[11],
        ])

    return pdf_response(
        "mediqueue_prescriptions.pdf",
        "MediQueue Prescription Report",
        f"Reporting period: {report_period_label(start_date, end_date)}",
        PRESCRIPTION_PDF_HEADERS,
        rows,
        PRESCRIPTION_PDF_WIDTHS,
    )
