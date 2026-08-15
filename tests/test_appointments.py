"""Automated availability and appointment workflow tests for MediQueue.

This chunk validates staff availability, generated appointment slots, patient
booking rules, cancellation, and the extra-appointment approval workflow.
"""

from datetime import date, timedelta

from app.extensions import db
from app.models import Appointment, AppointmentSlot, AvailabilityBlock


def login(client, account):
    """Log in a temporary test account through the real MediQueue API."""
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
    """Log out the currently authenticated test account."""
    response = client.post("/api/logout")
    assert response.status_code == 200
    assert response.get_json()["ok"] is True


def future_date(days=30):
    """Return a stable future date as ISO text for API payloads."""
    return (date.today() + timedelta(days=days)).isoformat()


def create_availability(
    client,
    *,
    days=30,
    start="09:00",
    end="10:00",
    duration=20,
    location="GP Practice",
):
    """Create availability through the same API used by the React frontend."""
    response = client.post(
        "/api/staff/availability",
        json={
            "date": future_date(days),
            "startTime": start,
            "endTime": end,
            "slotDuration": duration,
            "location": location,
        },
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["ok"] is True
    return body["availability"]


def book_slot(client, slot_id, reason="Automated appointment test"):
    """Book one slot through the patient-facing API."""
    return client.post(
        "/api/appointments/book",
        json={"slotId": slot_id, "reason": reason},
    )


def create_four_slot_schedule(client, doctor, *, days=40):
    """Create four non-overlapping 30-minute slots for one clinician."""
    login(client, doctor)
    availability = create_availability(
        client,
        days=days,
        start="09:00",
        end="11:00",
        duration=30,
    )
    logout(client)
    assert availability["slotCount"] == 4
    return availability


def book_four_appointments(client, patient, availability):
    """Book the four slots required to exercise the extra-booking rule."""
    login(client, patient)
    responses = []
    for slot in availability["slots"]:
        response = book_slot(client, slot["id"])
        assert response.status_code == 200
        responses.append(response)
    logout(client)
    return responses


def test_staff_availability_generates_expected_twenty_minute_slots(client, make_role_user):
    """A one-hour window with 20-minute duration must generate three slots."""
    doctor = make_role_user("Doctor")
    login(client, doctor)

    availability = create_availability(
        client,
        days=30,
        start="10:00",
        end="11:00",
        duration=20,
    )

    assert availability["slotCount"] == 3
    assert [slot["startTime"] for slot in availability["slots"]] == [
        "10:00",
        "10:20",
        "10:40",
    ]
    assert [slot["endTime"] for slot in availability["slots"]] == [
        "10:20",
        "10:40",
        "11:00",
    ]


def test_editing_slot_duration_regenerates_availability_slots(client, make_role_user):
    """Changing 20-minute slots to 30 minutes must regenerate 3 slots as 2."""
    doctor = make_role_user("Doctor")
    login(client, doctor)

    availability = create_availability(
        client,
        days=31,
        start="10:00",
        end="11:00",
        duration=20,
    )
    assert availability["slotCount"] == 3

    response = client.put(
        f"/api/staff/availability/{availability['id']}",
        json={
            "date": future_date(31),
            "startTime": "10:00",
            "endTime": "11:00",
            "slotDuration": 30,
            "location": "GP Practice",
        },
    )

    assert response.status_code == 200
    updated = response.get_json()["availability"]
    assert updated["slotDuration"] == 30
    assert updated["slotCount"] == 2
    assert [slot["startTime"] for slot in updated["slots"]] == ["10:00", "10:30"]
    assert [slot["endTime"] for slot in updated["slots"]] == ["10:30", "11:00"]


def test_overlapping_staff_availability_is_rejected(client, make_role_user):
    """The same clinician must not publish overlapping availability windows."""
    doctor = make_role_user("Doctor")
    login(client, doctor)

    create_availability(
        client,
        days=32,
        start="09:00",
        end="10:00",
        duration=20,
    )

    response = client.post(
        "/api/staff/availability",
        json={
            "date": future_date(32),
            "startTime": "09:30",
            "endTime": "10:30",
            "slotDuration": 20,
            "location": "GP Practice",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["ok"] is False
    assert "overlaps" in response.get_json()["error"].lower()


def test_invalid_availability_time_window_is_rejected(client, make_role_user):
    """Availability cannot finish before it starts."""
    doctor = make_role_user("Doctor")
    login(client, doctor)

    response = client.post(
        "/api/staff/availability",
        json={
            "date": future_date(33),
            "startTime": "11:00",
            "endTime": "10:00",
            "slotDuration": 20,
            "location": "GP Practice",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["ok"] is False
    assert "end time must be after start time" in response.get_json()["error"].lower()


def test_patient_can_view_generated_available_slots(client, make_role_user):
    """Published future staff slots must be visible to a logged-in patient."""
    doctor = make_role_user("Doctor")
    patient = make_role_user("Patient", email="available.patient@example.com")

    login(client, doctor)
    availability = create_availability(
        client,
        days=34,
        start="13:00",
        end="14:00",
        duration=30,
    )
    logout(client)

    login(client, patient)
    response = client.get(f"/api/appointments/available?date={future_date(34)}")

    assert response.status_code == 200
    body = response.get_json()
    assert body["ok"] is True
    returned_ids = {slot["id"] for slot in body["slots"]}
    expected_ids = {slot["id"] for slot in availability["slots"]}
    assert expected_ids.issubset(returned_ids)


def test_first_three_appointments_book_and_fourth_requires_approval(client, make_role_user):
    """The fourth active appointment with one clinician must be held for approval."""
    doctor = make_role_user("Doctor")
    patient = make_role_user("Patient", email="limit.patient@example.com")
    availability = create_four_slot_schedule(client, doctor, days=40)

    login(client, patient)
    statuses = []
    for slot in availability["slots"]:
        response = book_slot(client, slot["id"])
        assert response.status_code == 200
        statuses.append(response.get_json()["appointment"]["status"])

    assert statuses[:3] == ["Booked", "Booked", "Booked"]
    assert statuses[3] == "Pending Approval"


def test_booked_slot_cannot_be_booked_by_another_patient(client, make_role_user):
    """Once a slot is booked, another patient must not be able to take it."""
    doctor = make_role_user("Doctor")
    first_patient = make_role_user("Patient", email="first.patient@example.com")
    second_patient = make_role_user("Patient", email="second.patient@example.com")
    availability = create_four_slot_schedule(client, doctor, days=41)
    slot_id = availability["slots"][0]["id"]

    login(client, first_patient)
    first_response = book_slot(client, slot_id)
    assert first_response.status_code == 200
    logout(client)

    login(client, second_patient)
    second_response = book_slot(client, slot_id)

    assert second_response.status_code == 400
    assert second_response.get_json()["ok"] is False
    assert "already booked" in second_response.get_json()["error"].lower()


def test_patient_cannot_book_overlapping_time_with_different_clinician(client, make_role_user):
    """One patient must not hold two active appointments at the same time."""
    doctor_one = make_role_user("Doctor", email="doctor.one@example.com")
    doctor_two = make_role_user("Doctor", email="doctor.two@example.com")
    patient = make_role_user("Patient", email="overlap.patient@example.com")

    login(client, doctor_one)
    first = create_availability(
        client,
        days=42,
        start="10:00",
        end="10:30",
        duration=30,
    )
    logout(client)

    login(client, doctor_two)
    second = create_availability(
        client,
        days=42,
        start="10:00",
        end="10:30",
        duration=30,
    )
    logout(client)

    login(client, patient)
    first_booking = book_slot(client, first["slots"][0]["id"])
    assert first_booking.status_code == 200

    second_booking = book_slot(client, second["slots"][0]["id"])
    assert second_booking.status_code == 400
    assert "already have an appointment" in second_booking.get_json()["error"].lower()


def test_patient_cancellation_releases_future_slot(client, app, make_role_user):
    """Cancelling a future appointment must cancel the record and free its slot."""
    doctor = make_role_user("Doctor")
    patient = make_role_user("Patient", email="cancel.patient@example.com")
    availability = create_four_slot_schedule(client, doctor, days=43)

    login(client, patient)
    booking = book_slot(client, availability["slots"][0]["id"])
    assert booking.status_code == 200
    appointment_id = int(booking.get_json()["appointment"]["id"])

    response = client.post(f"/api/appointments/{appointment_id}/cancel")

    assert response.status_code == 200
    assert response.get_json()["appointment"]["status"] == "Cancelled"

    with app.app_context():
        appointment = db.session.get(Appointment, appointment_id)
        slot = db.session.get(AppointmentSlot, appointment.appointment_slot_id)
        assert appointment.status == "Cancelled"
        assert slot.status == "Available"


def test_patient_cannot_cancel_another_patients_appointment(client, make_role_user):
    """A patient must not be able to cancel an appointment owned by another patient."""
    doctor = make_role_user("Doctor")
    owner = make_role_user("Patient", email="owner.patient@example.com")
    intruder = make_role_user("Patient", email="intruder.patient@example.com")
    availability = create_four_slot_schedule(client, doctor, days=44)

    login(client, owner)
    booking = book_slot(client, availability["slots"][0]["id"])
    assert booking.status_code == 200
    appointment_id = int(booking.get_json()["appointment"]["id"])
    logout(client)

    login(client, intruder)
    response = client.post(f"/api/appointments/{appointment_id}/cancel")

    assert response.status_code == 403
    assert response.get_json()["ok"] is False
    assert "permission" in response.get_json()["error"].lower()


def test_staff_can_approve_pending_extra_appointment(client, app, make_role_user):
    """The assigned clinician can convert a fourth pending request into Booked."""
    doctor = make_role_user("Doctor")
    patient = make_role_user("Patient", email="approve.patient@example.com")
    availability = create_four_slot_schedule(client, doctor, days=45)
    responses = book_four_appointments(client, patient, availability)
    pending_id = int(responses[3].get_json()["appointment"]["id"])

    login(client, doctor)
    response = client.post(f"/api/staff/appointments/{pending_id}/approve-extra")

    assert response.status_code == 200
    assert response.get_json()["appointment"]["status"] == "Booked"

    with app.app_context():
        appointment = db.session.get(Appointment, pending_id)
        slot = db.session.get(AppointmentSlot, appointment.appointment_slot_id)
        assert appointment.status == "Booked"
        assert slot.status == "Booked"


def test_staff_can_reject_pending_extra_appointment_and_release_slot(client, app, make_role_user):
    """Rejecting a fourth request must mark it Rejected and make the slot Available."""
    doctor = make_role_user("Doctor")
    patient = make_role_user("Patient", email="reject.patient@example.com")
    availability = create_four_slot_schedule(client, doctor, days=46)
    responses = book_four_appointments(client, patient, availability)
    pending_id = int(responses[3].get_json()["appointment"]["id"])

    login(client, doctor)
    response = client.post(
        f"/api/staff/appointments/{pending_id}/reject-extra",
        json={"internalNote": "Not clinically required at this time."},
    )

    assert response.status_code == 200
    assert response.get_json()["appointment"]["status"] == "Rejected"

    with app.app_context():
        appointment = db.session.get(Appointment, pending_id)
        slot = db.session.get(AppointmentSlot, appointment.appointment_slot_id)
        assert appointment.status == "Rejected"
        assert appointment.internal_note == "Not clinically required at this time."
        assert slot.status == "Available"


def test_availability_linked_to_appointment_cannot_be_edited(client, make_role_user):
    """Once an appointment uses a block, that availability must become non-editable."""
    doctor = make_role_user("Doctor")
    patient = make_role_user("Patient", email="linked.patient@example.com")
    availability = create_four_slot_schedule(client, doctor, days=47)

    login(client, patient)
    booking = book_slot(client, availability["slots"][0]["id"])
    assert booking.status_code == 200
    logout(client)

    login(client, doctor)
    response = client.put(
        f"/api/staff/availability/{availability['id']}",
        json={
            "date": future_date(47),
            "startTime": "09:00",
            "endTime": "11:00",
            "slotDuration": 20,
            "location": "Updated room",
        },
    )

    assert response.status_code == 409
    assert response.get_json()["ok"] is False
    assert "linked to appointments" in response.get_json()["error"].lower()


def test_different_staff_member_cannot_approve_someone_elses_pending_request(client, make_role_user):
    """A clinician cannot approve an extra request assigned to another clinician."""
    assigned_doctor = make_role_user("Doctor", email="assigned.doctor@example.com")
    other_doctor = make_role_user("Doctor", email="other.doctor@example.com")
    patient = make_role_user("Patient", email="staffcheck.patient@example.com")
    availability = create_four_slot_schedule(client, assigned_doctor, days=48)
    responses = book_four_appointments(client, patient, availability)
    pending_id = int(responses[3].get_json()["appointment"]["id"])

    login(client, other_doctor)
    response = client.post(f"/api/staff/appointments/{pending_id}/approve-extra")

    assert response.status_code == 403
    assert response.get_json()["ok"] is False
    assert "assigned to you" in response.get_json()["error"].lower()
