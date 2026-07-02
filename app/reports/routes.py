import csv
from io import StringIO

from flask import Response, render_template
from flask_login import login_required

from app.decorators import role_required
from app.models import Appointment, AppointmentSlot, PatientProfile, Prescription, StaffProfile
from app.reports import reports_bp


def _format_datetime(value, fmt="%d %b %Y %H:%M"):
    if not value:
        return ""
    return value.strftime(fmt)


def _csv_response(filename, rows):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerows(rows)

    response = Response(output.getvalue(), mimetype="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@reports_bp.route("/")
@login_required
@role_required("Practice Admin")
def index():
    total_appointments = Appointment.query.count()
    booked_appointments = Appointment.query.filter_by(status="Booked").count()
    completed_appointments = Appointment.query.filter_by(status="Completed").count()
    cancelled_appointments = Appointment.query.filter_by(status="Cancelled").count()

    total_prescriptions = Prescription.query.count()
    pending_prescriptions = Prescription.query.filter(Prescription.status.in_(["Requested", "Under Review"])).count()
    paid_prescriptions = Prescription.query.filter_by(payment_status="Paid").count()

    latest_appointments = (
        Appointment.query.join(Appointment.slot)
        .order_by(AppointmentSlot.start_at.desc())
        .limit(5)
        .all()
    )
    latest_prescriptions = Prescription.query.order_by(Prescription.created_at.desc()).limit(5).all()

    return render_template(
        "admin/reports.html",
        total_patients=PatientProfile.query.count(),
        total_staff=StaffProfile.query.count(),
        total_appointments=total_appointments,
        booked_appointments=booked_appointments,
        completed_appointments=completed_appointments,
        cancelled_appointments=cancelled_appointments,
        total_prescriptions=total_prescriptions,
        pending_prescriptions=pending_prescriptions,
        paid_prescriptions=paid_prescriptions,
        latest_appointments=latest_appointments,
        latest_prescriptions=latest_prescriptions,
    )


@reports_bp.route("/appointments.csv")
@login_required
@role_required("Practice Admin")
def appointments_csv():
    appointments = (
        Appointment.query.join(Appointment.slot)
        .order_by(AppointmentSlot.start_at.desc())
        .all()
    )

    rows = [[
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
    ]]

    for appointment in appointments:
        slot = appointment.slot
        rows.append([
            appointment.id,
            _format_datetime(slot.start_at, "%Y-%m-%d") if slot else "",
            _format_datetime(slot.start_at, "%H:%M") if slot else "",
            _format_datetime(slot.end_at, "%H:%M") if slot else "",
            appointment.patient_profile.user.full_name,
            appointment.patient_profile.user.email,
            appointment.staff_profile.user.full_name,
            appointment.staff_profile.job_title,
            appointment.reason or "",
            appointment.status,
            _format_datetime(appointment.created_at),
        ])

    return _csv_response("mediqueue_appointments.csv", rows)


@reports_bp.route("/prescriptions.csv")
@login_required
@role_required("Practice Admin")
def prescriptions_csv():
    prescriptions = Prescription.query.order_by(Prescription.created_at.desc()).all()

    rows = [[
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
    ]]

    for prescription in prescriptions:
        reviewer = prescription.reviewed_by_staff.user.full_name if prescription.reviewed_by_staff else ""
        rows.append([
            prescription.id,
            _format_datetime(prescription.created_at),
            prescription.patient_profile.user.full_name,
            prescription.patient_profile.user.email,
            prescription.medicine_name,
            prescription.quantity,
            prescription.reason or "",
            prescription.status,
            prescription.payment_status,
            f"{prescription.amount_due:.2f}" if prescription.amount_due else "0.00",
            prescription.payment_reference or "",
            reviewer,
            _format_datetime(prescription.reviewed_at),
        ])

    return _csv_response("mediqueue_prescriptions.csv", rows)
