"""Automated report, CSV/PDF export, and calendar export tests for MediQueue.

Testing Chunk 6 validates reporting filters and summary counts, downloadable
appointment/prescription reports, and iCalendar (.ics) exports while preserving
role-based access restrictions.
"""

from datetime import date, datetime, time, timedelta
import csv
import io

import pytest

from app.extensions import db
from app.models import (
    Appointment,
    AppointmentSlot,
    AvailabilityBlock,
    PatientProfile,
    Prescription,
    StaffProfile,
)




def unfold_ics(text):
    """Return logical iCalendar content with RFC-style folded lines joined."""
    return text.replace("\r\n ", "").replace("\r\n\t", "").replace("\n ", "").replace("\n\t", "")

def login(client, account):
    """Log in one temporary MediQueue account through the real API."""
    response = client.post(
        "/api/login",
        json={
            "email": account["email"],
            "password": account["password"],
            "remember": False,
        },
    )
    assert response.status_code == 200
    assert response.get_json()["ok"] is True
    return response


def logout(client):
    """End the current API session when a test changes user."""
    response = client.post("/api/logout")
    assert response.status_code == 200
    assert response.get_json()["ok"] is True


def create_appointment_record(
    app,
    patient,
    clinician,
    *,
    start_at,
    status="Booked",
    reason="Automated report test",
    location="GP Practice",
):
    """Create one complete appointment record directly in the isolated test DB."""
    with app.app_context():
        patient_profile = PatientProfile.query.filter_by(user_id=patient["id"]).one()
        staff_profile = StaffProfile.query.filter_by(user_id=clinician["id"]).one()
        end_at = start_at + timedelta(minutes=30)

        availability = AvailabilityBlock(
            staff_profile_id=staff_profile.id,
            available_date=start_at.date(),
            start_time=start_at.time(),
            end_time=end_at.time(),
            slot_duration_minutes=30,
            location=location,
        )
        db.session.add(availability)
        db.session.flush()

        slot = AppointmentSlot(
            availability_block_id=availability.id,
            start_at=start_at,
            end_at=end_at,
            status="Booked" if status == "Booked" else "Available",
        )
        db.session.add(slot)
        db.session.flush()

        appointment = Appointment(
            patient_profile_id=patient_profile.id,
            staff_profile_id=staff_profile.id,
            appointment_slot_id=slot.id,
            status=status,
            reason=reason,
        )
        db.session.add(appointment)
        db.session.commit()
        return appointment.id


def create_prescription_record(
    app,
    patient,
    *,
    created_at,
    medicine="Amoxicillin",
    quantity="21 tablets",
    status="Requested",
    payment_status="Not Required",
    amount_due=0.0,
    payment_reference=None,
):
    """Create one prescription record for report/filter testing."""
    with app.app_context():
        patient_profile = PatientProfile.query.filter_by(user_id=patient["id"]).one()
        prescription = Prescription(
            patient_profile_id=patient_profile.id,
            medicine_name=medicine,
            quantity=quantity,
            reason="Automated report test",
            status=status,
            payment_status=payment_status,
            amount_due=amount_due,
            payment_reference=payment_reference,
            created_at=created_at,
        )
        db.session.add(prescription)
        db.session.commit()
        return prescription.id


def test_report_summary_is_restricted_to_practice_admin(client, make_role_user):
    """Patients must not be able to retrieve administrative reporting data."""
    patient = make_role_user("Patient")
    login(client, patient)

    response = client.get("/api/reports/summary")

    assert response.status_code == 403
    assert response.get_json()["ok"] is False
    assert "practice admin" in response.get_json()["error"].lower()


def test_admin_report_summary_counts_appointment_and_prescription_statuses(
    client, app, make_role_user
):
    """Summary metrics must reflect the records currently stored in MediQueue."""
    admin = make_role_user("Practice Admin")
    patient = make_role_user("Patient", email="summary.patient@example.com")
    doctor = make_role_user("Doctor", email="summary.doctor@example.com")
    base = datetime.combine(date.today() + timedelta(days=20), time(9, 0))

    create_appointment_record(app, patient, doctor, start_at=base, status="Booked")
    create_appointment_record(
        app, patient, doctor, start_at=base + timedelta(days=1), status="Completed"
    )
    create_appointment_record(
        app, patient, doctor, start_at=base + timedelta(days=2), status="Cancelled"
    )

    create_prescription_record(
        app,
        patient,
        created_at=datetime.now(),
        medicine="Requested Medicine",
        status="Requested",
    )
    create_prescription_record(
        app,
        patient,
        created_at=datetime.now(),
        medicine="Approved Medicine",
        status="Approved",
        payment_status="Pending",
        amount_due=9.90,
    )
    create_prescription_record(
        app,
        patient,
        created_at=datetime.now(),
        medicine="Paid Medicine",
        status="Ready for Collection",
        payment_status="Paid",
        amount_due=9.90,
        payment_reference="MQPAY-REPORT-001",
    )

    login(client, admin)
    response = client.get("/api/reports/summary")

    assert response.status_code == 200
    summary = response.get_json()["summary"]
    assert summary["appointments"] == 3
    assert summary["bookedAppointments"] == 1
    assert summary["completedAppointments"] == 1
    assert summary["cancelledAppointments"] == 1
    assert summary["prescriptions"] == 3
    assert summary["requestedPrescriptions"] == 1
    assert summary["approvedPrescriptions"] == 1
    assert summary["readyPrescriptions"] == 1
    assert summary["pendingPaymentPrescriptions"] == 1
    assert summary["paidPrescriptions"] == 1


def test_report_summary_date_filter_includes_only_selected_period(
    client, app, make_role_user
):
    """Date filters must exclude appointment and prescription records outside the period."""
    admin = make_role_user("Practice Admin")
    patient = make_role_user("Patient", email="filter.patient@example.com")
    doctor = make_role_user("Doctor", email="filter.doctor@example.com")

    selected_day = date.today() + timedelta(days=10)
    outside_day = selected_day + timedelta(days=20)
    create_appointment_record(
        app,
        patient,
        doctor,
        start_at=datetime.combine(selected_day, time(10, 0)),
        reason="Included appointment",
    )
    create_appointment_record(
        app,
        patient,
        doctor,
        start_at=datetime.combine(outside_day, time(10, 0)),
        reason="Excluded appointment",
    )

    create_prescription_record(
        app,
        patient,
        created_at=datetime.combine(selected_day, time(12, 0)),
        medicine="Included Medicine",
    )
    create_prescription_record(
        app,
        patient,
        created_at=datetime.combine(outside_day, time(12, 0)),
        medicine="Excluded Medicine",
    )

    login(client, admin)
    response = client.get(
        "/api/reports/summary",
        query_string={
            "start_date": selected_day.isoformat(),
            "end_date": selected_day.isoformat(),
        },
    )

    assert response.status_code == 200
    summary = response.get_json()["summary"]
    assert summary["appointments"] == 1
    assert summary["prescriptions"] == 1
    assert summary["filters"] == {
        "start_date": selected_day.isoformat(),
        "end_date": selected_day.isoformat(),
    }


@pytest.mark.parametrize(
    "query_string",
    [
        {"start_date": "not-a-date"},
        {"end_date": "2026-99-99"},
    ],
)
def test_report_summary_rejects_invalid_date_format(client, make_role_user, query_string):
    """Malformed report dates must produce a controlled 400 response."""
    admin = make_role_user("Practice Admin")
    login(client, admin)

    response = client.get("/api/reports/summary", query_string=query_string)

    assert response.status_code == 400
    assert response.get_json()["ok"] is False
    assert "valid" in response.get_json()["error"].lower()


def test_report_summary_rejects_start_date_after_end_date(client, make_role_user):
    """A reporting range with start > end must be rejected."""
    admin = make_role_user("Practice Admin")
    login(client, admin)

    response = client.get(
        "/api/reports/summary",
        query_string={"start_date": "2026-08-20", "end_date": "2026-08-10"},
    )

    assert response.status_code == 400
    assert "cannot be after" in response.get_json()["error"].lower()


def test_admin_can_download_appointment_csv(client, app, make_role_user):
    """Appointment CSV export must return a downloadable file containing report data."""
    admin = make_role_user("Practice Admin")
    patient = make_role_user("Patient", email="csv.patient@example.com")
    doctor = make_role_user(
        "Doctor",
        email="csv.doctor@example.com",
        first_name="CSV",
        last_name="Doctor",
    )
    start_at = datetime.combine(date.today() + timedelta(days=15), time(11, 30))
    appointment_id = create_appointment_record(
        app,
        patient,
        doctor,
        start_at=start_at,
        reason="CSV export reason",
    )

    login(client, admin)
    response = client.get("/reports/appointments.csv")

    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert "mediqueue_appointments.csv" in response.headers["Content-Disposition"]
    text = response.get_data(as_text=True)
    assert "Appointment ID" in text
    assert str(appointment_id) in text
    assert "CSV Doctor" in text
    assert "CSV export reason" in text


def test_appointment_csv_respects_date_filter(client, app, make_role_user):
    """Filtered appointment CSV output must exclude rows outside the requested date."""
    admin = make_role_user("Practice Admin")
    patient = make_role_user("Patient", email="csv.filter.patient@example.com")
    doctor = make_role_user("Doctor", email="csv.filter.doctor@example.com")
    included_day = date.today() + timedelta(days=25)
    excluded_day = included_day + timedelta(days=5)

    included_id = create_appointment_record(
        app,
        patient,
        doctor,
        start_at=datetime.combine(included_day, time(9, 0)),
        reason="INCLUDED-CSV-ROW",
    )
    excluded_id = create_appointment_record(
        app,
        patient,
        doctor,
        start_at=datetime.combine(excluded_day, time(9, 0)),
        reason="EXCLUDED-CSV-ROW",
    )

    login(client, admin)
    response = client.get(
        "/reports/appointments.csv",
        query_string={
            "start_date": included_day.isoformat(),
            "end_date": included_day.isoformat(),
        },
    )

    assert response.status_code == 200
    text = response.get_data(as_text=True)
    rows = list(csv.DictReader(io.StringIO(text)))

    assert any(
        row["Appointment ID"] == str(included_id)
        and row["Reason"] == "INCLUDED-CSV-ROW"
        for row in rows
    )
    assert not any(
        row["Appointment ID"] == str(excluded_id)
        or row["Reason"] == "EXCLUDED-CSV-ROW"
        for row in rows
    )


def test_admin_can_download_prescription_csv(client, app, make_role_user):
    """Prescription CSV export must include prescription and payment information."""
    admin = make_role_user("Practice Admin")
    patient = make_role_user("Patient", email="prescription.csv@example.com")
    prescription_id = create_prescription_record(
        app,
        patient,
        created_at=datetime.now(),
        medicine="CSV Medicine",
        quantity="28 tablets",
        status="Approved",
        payment_status="Pending",
        amount_due=9.90,
    )

    login(client, admin)
    response = client.get("/reports/prescriptions.csv")

    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert "mediqueue_prescriptions.csv" in response.headers["Content-Disposition"]
    text = response.get_data(as_text=True)
    assert "Prescription ID" in text
    assert str(prescription_id) in text
    assert "CSV Medicine" in text
    assert "9.90" in text


def test_admin_can_download_appointment_pdf(client, app, make_role_user):
    """Appointment PDF export must return a real PDF download rather than redirecting."""
    admin = make_role_user("Practice Admin")
    patient = make_role_user("Patient", email="appointment.pdf@example.com")
    doctor = make_role_user("Doctor", email="appointment.pdf.doctor@example.com")
    create_appointment_record(
        app,
        patient,
        doctor,
        start_at=datetime.combine(date.today() + timedelta(days=18), time(14, 0)),
    )

    login(client, admin)
    response = client.get("/reports/appointments.pdf")

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert "mediqueue_appointments.pdf" in response.headers["Content-Disposition"]
    assert response.data.startswith(b"%PDF")
    assert len(response.data) > 500


def test_admin_can_download_prescription_pdf(client, app, make_role_user):
    """Prescription PDF export must return a generated PDF file."""
    admin = make_role_user("Practice Admin")
    patient = make_role_user("Patient", email="prescription.pdf@example.com")
    create_prescription_record(
        app,
        patient,
        created_at=datetime.now(),
        medicine="PDF Medicine",
        status="Requested",
    )

    login(client, admin)
    response = client.get("/reports/prescriptions.pdf")

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert "mediqueue_prescriptions.pdf" in response.headers["Content-Disposition"]
    assert response.data.startswith(b"%PDF")
    assert len(response.data) > 500


@pytest.mark.parametrize(
    "url",
    [
        "/reports/appointments.csv",
        "/reports/appointments.pdf",
        "/reports/prescriptions.csv",
        "/reports/prescriptions.pdf",
    ],
)
def test_non_admin_cannot_download_reports(client, make_role_user, url):
    """Report downloads must remain restricted to Practice Admin users."""
    patient = make_role_user("Patient")
    login(client, patient)

    response = client.get(url)

    assert response.status_code == 403


def test_patient_can_export_own_booked_appointment_as_ics(client, app, make_role_user):
    """The owning patient can download a confirmed appointment as iCalendar."""
    patient = make_role_user(
        "Patient",
        email="calendar.patient@example.com",
        first_name="Calendar",
        last_name="Patient",
    )
    doctor = make_role_user(
        "Doctor",
        email="calendar.doctor@example.com",
        first_name="Calendar",
        last_name="Doctor",
    )
    start_at = datetime.combine(date.today() + timedelta(days=12), time(10, 0))
    appointment_id = create_appointment_record(
        app,
        patient,
        doctor,
        start_at=start_at,
        status="Booked",
        reason="Calendar export test",
        location="Room 5",
    )

    login(client, patient)
    response = client.get(f"/api/appointments/{appointment_id}/calendar")

    assert response.status_code == 200
    assert response.mimetype == "text/calendar"
    assert f"mediqueue-appointment-{appointment_id}.ics" in response.headers["Content-Disposition"]
    text = unfold_ics(response.get_data(as_text=True))
    assert "BEGIN:VCALENDAR" in text
    assert "BEGIN:VEVENT" in text
    assert "Calendar Doctor" in text
    assert "Calendar export test" in text
    assert "LOCATION:Room 5" in text
    assert "STATUS:CONFIRMED" in text
    assert "END:VCALENDAR" in text


def test_patient_cannot_export_another_patients_calendar(client, app, make_role_user):
    """Calendar downloads must respect appointment ownership."""
    owner = make_role_user("Patient", email="calendar.owner@example.com")
    intruder = make_role_user("Patient", email="calendar.intruder@example.com")
    doctor = make_role_user("Doctor", email="calendar.owner.doctor@example.com")
    appointment_id = create_appointment_record(
        app,
        owner,
        doctor,
        start_at=datetime.combine(date.today() + timedelta(days=13), time(10, 0)),
    )

    login(client, intruder)
    response = client.get(f"/api/appointments/{appointment_id}/calendar")

    assert response.status_code == 403
    assert "permission" in response.get_json()["error"].lower()


def test_non_booked_appointment_cannot_be_exported_to_calendar(
    client, app, make_role_user
):
    """Pending/rejected/cancelled appointments must not be exported as confirmed events."""
    patient = make_role_user("Patient", email="calendar.pending@example.com")
    doctor = make_role_user("Doctor", email="calendar.pending.doctor@example.com")
    appointment_id = create_appointment_record(
        app,
        patient,
        doctor,
        start_at=datetime.combine(date.today() + timedelta(days=14), time(10, 0)),
        status="Pending Approval",
    )

    login(client, patient)
    response = client.get(f"/api/appointments/{appointment_id}/calendar")

    assert response.status_code == 400
    assert "confirmed booked appointments" in response.get_json()["error"].lower()


def test_staff_schedule_calendar_contains_only_logged_in_clinicians_bookings(
    client, app, make_role_user
):
    """A staff calendar export must not include another clinician's appointments."""
    patient = make_role_user("Patient", email="staff.calendar.patient@example.com")
    doctor_one = make_role_user(
        "Doctor",
        email="staff.calendar.one@example.com",
        first_name="Doctor",
        last_name="One",
    )
    doctor_two = make_role_user(
        "Doctor",
        email="staff.calendar.two@example.com",
        first_name="Doctor",
        last_name="Two",
    )
    day = date.today() + timedelta(days=16)
    own_id = create_appointment_record(
        app,
        patient,
        doctor_one,
        start_at=datetime.combine(day, time(9, 0)),
        reason="OWN-STAFF-CALENDAR",
    )
    other_id = create_appointment_record(
        app,
        patient,
        doctor_two,
        start_at=datetime.combine(day, time(11, 0)),
        reason="OTHER-STAFF-CALENDAR",
    )

    login(client, doctor_one)
    response = client.get(
        "/api/staff/schedule/calendar",
        query_string={"from": day.isoformat(), "to": day.isoformat()},
    )

    assert response.status_code == 200
    assert response.mimetype == "text/calendar"
    text = unfold_ics(response.get_data(as_text=True))
    assert f"UID:mediqueue-appointment-{own_id}@mediqueue.local" in text
    assert "OWN-STAFF-CALENDAR" in text
    assert f"UID:mediqueue-appointment-{other_id}@mediqueue.local" not in text
    assert "OTHER-STAFF-CALENDAR" not in text


def test_staff_schedule_calendar_rejects_invalid_date(client, make_role_user):
    """Malformed staff calendar filter dates must be rejected cleanly."""
    doctor = make_role_user("Doctor")
    login(client, doctor)

    response = client.get("/api/staff/schedule/calendar?from=bad-date")

    assert response.status_code == 400
    assert "valid calendar export dates" in response.get_json()["error"].lower()


def test_patient_cannot_export_staff_schedule_calendar(client, make_role_user):
    """The multi-appointment staff calendar endpoint is restricted to doctors/nurses."""
    patient = make_role_user("Patient")
    login(client, patient)

    response = client.get("/api/staff/schedule/calendar")

    assert response.status_code == 403
    assert "staff access required" in response.get_json()["error"].lower()
