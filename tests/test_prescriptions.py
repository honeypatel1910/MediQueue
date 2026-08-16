"""Automated prescription, payment, notification, and collection workflow tests.

This chunk validates the React-facing Flask APIs used by MediQueue for patient
prescription requests, doctor review, simulated payment, practice-admin
collection updates, in-app notifications, and related audit records.
"""

from app.extensions import db
from app.models import AuditLog, Notification, Prescription, User
from app.prescriptions.routes import PRESCRIPTION_STANDARD_FEE


def login(client, account):
    """Log in a temporary MediQueue account through the real API."""
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


def request_prescription(client, medicine="Amoxicillin", quantity="21 tablets", reason="Test request"):
    """Create a prescription request through the patient API."""
    return client.post(
        "/api/prescriptions/request",
        json={
            "medicine": medicine,
            "quantity": quantity,
            "reason": reason,
        },
    )


def create_requested_prescription(client, patient, **kwargs):
    """Log in as patient and return the id of a newly requested prescription."""
    login(client, patient)
    response = request_prescription(client, **kwargs)
    assert response.status_code == 201
    return int(response.get_json()["prescription"]["id"])


def review_prescription(client, prescription_id, status):
    """Submit a doctor review through the React-facing API."""
    return client.post(
        f"/api/prescriptions/{prescription_id}/review",
        json={"status": status},
    )


def request_and_approve(client, patient, doctor):
    """Create a patient request and approve it as a doctor."""
    prescription_id = create_requested_prescription(client, patient)
    logout(client)
    login(client, doctor)
    response = review_prescription(client, prescription_id, "Approved")
    assert response.status_code == 200
    assert response.get_json()["prescription"]["status"] == "Approved"
    logout(client)
    return prescription_id


def request_approve_and_pay(client, patient, doctor, method="card"):
    """Complete request -> approval -> simulated payment and return prescription id."""
    prescription_id = request_and_approve(client, patient, doctor)
    login(client, patient)
    response = client.post(
        f"/api/prescriptions/{prescription_id}/pay",
        json={"method": method},
    )
    assert response.status_code == 200
    assert response.get_json()["prescription"]["paymentStatus"] == "Paid"
    logout(client)
    return prescription_id


def test_prescription_request_requires_medicine_and_quantity(client, make_role_user):
    """A patient cannot submit an incomplete prescription request."""
    patient = make_role_user("Patient")
    login(client, patient)

    response = client.post(
        "/api/prescriptions/request",
        json={"medicine": "", "quantity": "", "reason": "Missing fields"},
    )

    assert response.status_code == 400
    assert response.get_json()["ok"] is False
    assert "required" in response.get_json()["error"].lower()


def test_patient_request_creates_prescription_notifications_and_audit_log(
    client, app, make_role_user
):
    """A valid request must persist the workflow and notify patient + doctor."""
    patient = make_role_user("Patient", email="rx.patient@example.com")
    doctor = make_role_user("Doctor", email="rx.doctor@example.com")
    login(client, patient)

    response = request_prescription(
        client,
        medicine="Amoxicillin",
        quantity="21 tablets",
        reason="Repeat prescription",
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["ok"] is True
    assert body["prescription"]["status"] == "Requested"
    assert body["prescription"]["paymentStatus"] == "Not required"

    prescription_id = int(body["prescription"]["id"])
    with app.app_context():
        prescription = db.session.get(Prescription, prescription_id)
        assert prescription is not None
        assert prescription.medicine_name == "Amoxicillin"
        assert prescription.quantity == "21 tablets"
        assert prescription.payment_status == "Not Required"
        assert prescription.amount_due == 0.0

        patient_notice = Notification.query.filter_by(
            user_id=patient["id"], title="Prescription request submitted"
        ).first()
        doctor_notice = Notification.query.filter_by(
            user_id=doctor["id"], title="New prescription request"
        ).first()
        assert patient_notice is not None
        assert doctor_notice is not None

        audit = AuditLog.query.filter_by(
            action="Prescription requested",
            entity_type="Prescription",
            entity_id=prescription_id,
        ).first()
        assert audit is not None


def test_non_patient_cannot_request_prescription(client, make_role_user):
    """Clinical/admin roles must not use the patient prescription-request API."""
    doctor = make_role_user("Doctor")
    login(client, doctor)

    response = request_prescription(client)

    assert response.status_code == 403
    assert response.get_json()["error"] == "Patient access required."


def test_patient_prescription_list_contains_only_their_own_requests(
    client, make_role_user
):
    """Patients must not see another patient's prescription history."""
    patient_one = make_role_user("Patient", email="patient.one.rx@example.com")
    patient_two = make_role_user("Patient", email="patient.two.rx@example.com")

    first_id = create_requested_prescription(
        client, patient_one, medicine="Medicine One", quantity="10"
    )
    logout(client)
    second_id = create_requested_prescription(
        client, patient_two, medicine="Medicine Two", quantity="20"
    )

    response = client.get("/api/prescriptions")

    assert response.status_code == 200
    ids = {int(item["id"]) for item in response.get_json()["prescriptions"]}
    assert second_id in ids
    assert first_id not in ids


def test_doctor_can_view_prescription_review_queue(client, make_role_user):
    """Doctors can retrieve requested prescriptions for clinical review."""
    patient = make_role_user("Patient", email="queue.patient@example.com")
    doctor = make_role_user("Doctor", email="queue.doctor@example.com")
    prescription_id = create_requested_prescription(client, patient)
    logout(client)
    login(client, doctor)

    response = client.get("/api/prescriptions")

    assert response.status_code == 200
    assert response.get_json()["ok"] is True
    ids = {int(item["id"]) for item in response.get_json()["prescriptions"]}
    assert prescription_id in ids


def test_patient_cannot_review_prescription(client, make_role_user):
    """Only doctors can update clinical prescription-review status."""
    patient = make_role_user("Patient")
    prescription_id = create_requested_prescription(client, patient)

    response = review_prescription(client, prescription_id, "Approved")

    assert response.status_code == 403
    assert response.get_json()["error"] == "Doctor access required."


def test_invalid_doctor_review_status_is_rejected(client, make_role_user):
    """Doctor review is restricted to the application's allowed statuses."""
    patient = make_role_user("Patient", email="invalid.status.patient@example.com")
    doctor = make_role_user("Doctor", email="invalid.status.doctor@example.com")
    prescription_id = create_requested_prescription(client, patient)
    logout(client)
    login(client, doctor)

    response = review_prescription(client, prescription_id, "Collected")

    assert response.status_code == 400
    assert response.get_json()["ok"] is False
    assert "invalid prescription status" in response.get_json()["error"].lower()


def test_doctor_can_move_prescription_under_review(client, app, make_role_user):
    """Under Review records the reviewer but does not create a payment due."""
    patient = make_role_user("Patient", email="review.patient@example.com")
    doctor = make_role_user("Doctor", email="review.doctor@example.com")
    prescription_id = create_requested_prescription(client, patient)
    logout(client)
    login(client, doctor)

    response = review_prescription(client, prescription_id, "Under Review")

    assert response.status_code == 200
    data = response.get_json()["prescription"]
    assert data["status"] == "Under Review"
    assert data["paymentStatus"] == "Not required"
    assert data["amountDue"] == 0.0

    with app.app_context():
        prescription = db.session.get(Prescription, prescription_id)
        assert prescription.reviewed_by_staff_profile_id is not None
        assert prescription.reviewed_at is not None
        assert Notification.query.filter_by(
            user_id=patient["id"], title="Prescription updated"
        ).first() is not None


def test_doctor_approval_creates_standard_payment_due(client, app, make_role_user):
    """Approving a prescription must create the configured standard payment."""
    patient = make_role_user("Patient", email="approve.rx.patient@example.com")
    doctor = make_role_user("Doctor", email="approve.rx.doctor@example.com")
    prescription_id = create_requested_prescription(client, patient)
    logout(client)
    login(client, doctor)

    response = review_prescription(client, prescription_id, "Approved")

    assert response.status_code == 200
    data = response.get_json()["prescription"]
    assert data["status"] == "Approved"
    assert data["paymentStatus"] == "Pending"
    assert data["amountDue"] == PRESCRIPTION_STANDARD_FEE

    with app.app_context():
        prescription = db.session.get(Prescription, prescription_id)
        assert prescription.payment_status == "Pending"
        assert prescription.amount_due == PRESCRIPTION_STANDARD_FEE
        assert prescription.reviewed_by_staff_profile_id is not None

        audit = AuditLog.query.filter_by(
            action="Prescription reviewed", entity_id=prescription_id
        ).first()
        assert audit is not None


def test_doctor_rejection_removes_payment_requirement(client, app, make_role_user):
    """Rejected prescriptions must not leave a patient payment due."""
    patient = make_role_user("Patient", email="reject.rx.patient@example.com")
    doctor = make_role_user("Doctor", email="reject.rx.doctor@example.com")
    prescription_id = create_requested_prescription(client, patient)
    logout(client)
    login(client, doctor)

    response = review_prescription(client, prescription_id, "Rejected")

    assert response.status_code == 200
    data = response.get_json()["prescription"]
    assert data["status"] == "Rejected"
    assert data["paymentStatus"] == "Not required"
    assert data["amountDue"] == 0.0

    with app.app_context():
        prescription = db.session.get(Prescription, prescription_id)
        assert prescription.payment_status == "Not Required"
        assert prescription.amount_due == 0.0


def test_patient_cannot_pay_before_doctor_approval(client, make_role_user):
    """A Requested prescription has no payable amount and must reject payment."""
    patient = make_role_user("Patient")
    prescription_id = create_requested_prescription(client, patient)

    response = client.post(
        f"/api/prescriptions/{prescription_id}/pay",
        json={"method": "card"},
    )

    assert response.status_code == 400
    assert response.get_json()["ok"] is False
    assert "no payment due" in response.get_json()["error"].lower()


def test_patient_cannot_pay_another_patients_prescription(client, make_role_user):
    """Prescription payment must be restricted to the owning patient."""
    owner = make_role_user("Patient", email="owner.rx@example.com")
    intruder = make_role_user("Patient", email="intruder.rx@example.com")
    doctor = make_role_user("Doctor", email="payment.doctor@example.com")
    prescription_id = request_and_approve(client, owner, doctor)
    login(client, intruder)

    response = client.post(
        f"/api/prescriptions/{prescription_id}/pay",
        json={"method": "card"},
    )

    assert response.status_code == 403
    assert response.get_json()["ok"] is False
    assert "your own" in response.get_json()["error"].lower()


def test_simulated_payment_records_method_reference_time_notification_and_audit(
    client, app, make_role_user
):
    """Successful simulated payment must persist all important payment evidence."""
    patient = make_role_user("Patient", email="paid.rx.patient@example.com")
    doctor = make_role_user("Doctor", email="paid.rx.doctor@example.com")
    prescription_id = request_and_approve(client, patient, doctor)
    login(client, patient)

    response = client.post(
        f"/api/prescriptions/{prescription_id}/pay",
        json={"method": "card"},
    )

    assert response.status_code == 200
    data = response.get_json()["prescription"]
    assert data["paymentStatus"] == "Paid"
    assert data["paymentReference"].startswith("MQPAY-")

    with app.app_context():
        prescription = db.session.get(Prescription, prescription_id)
        assert prescription.payment_status == "Paid"
        assert prescription.payment_method == "card"
        assert prescription.payment_reference.startswith("MQPAY-")
        assert prescription.paid_at is not None

        assert Notification.query.filter_by(
            user_id=patient["id"], title="Prescription payment received"
        ).first() is not None
        assert AuditLog.query.filter_by(
            action="Prescription payment completed", entity_id=prescription_id
        ).first() is not None


def test_repeated_payment_is_idempotent_and_keeps_original_reference(
    client, make_role_user
):
    """Submitting payment twice must not generate a second payment reference."""
    patient = make_role_user("Patient", email="repeat.payment.patient@example.com")
    doctor = make_role_user("Doctor", email="repeat.payment.doctor@example.com")
    prescription_id = request_and_approve(client, patient, doctor)
    login(client, patient)

    first = client.post(
        f"/api/prescriptions/{prescription_id}/pay",
        json={"method": "card"},
    )
    assert first.status_code == 200
    first_reference = first.get_json()["prescription"]["paymentReference"]

    second = client.post(
        f"/api/prescriptions/{prescription_id}/pay",
        json={"method": "bank_transfer"},
    )

    assert second.status_code == 200
    data = second.get_json()["prescription"]
    assert data["paymentStatus"] == "Paid"
    assert data["paymentReference"] == first_reference


def test_admin_cannot_mark_unpaid_prescription_ready_for_collection(
    client, make_role_user
):
    """Collection workflow cannot begin until approval and payment are complete."""
    patient = make_role_user("Patient", email="unpaid.ready.patient@example.com")
    doctor = make_role_user("Doctor", email="unpaid.ready.doctor@example.com")
    admin = make_role_user("Practice Admin", email="unpaid.ready.admin@example.com")
    prescription_id = request_and_approve(client, patient, doctor)
    login(client, admin)

    response = client.post(
        f"/api/admin/prescriptions/{prescription_id}/status",
        json={"status": "Ready for Collection"},
    )

    assert response.status_code == 400
    assert response.get_json()["ok"] is False
    assert "approved and paid" in response.get_json()["error"].lower()


def test_admin_can_mark_paid_prescription_ready_for_collection(
    client, app, make_role_user
):
    """A paid approved prescription can progress to Ready for Collection."""
    patient = make_role_user("Patient", email="ready.patient@example.com")
    doctor = make_role_user("Doctor", email="ready.doctor@example.com")
    admin = make_role_user("Practice Admin", email="ready.admin@example.com")
    prescription_id = request_approve_and_pay(client, patient, doctor)
    login(client, admin)

    response = client.post(
        f"/api/admin/prescriptions/{prescription_id}/status",
        json={"status": "Ready for Collection"},
    )

    assert response.status_code == 200
    assert response.get_json()["prescription"]["status"] == "Ready for Collection"

    with app.app_context():
        prescription = db.session.get(Prescription, prescription_id)
        assert prescription.status == "Ready for Collection"
        assert Notification.query.filter_by(
            user_id=patient["id"], title="Prescription status updated"
        ).first() is not None
        assert AuditLog.query.filter_by(
            action="Prescription collection status updated", entity_id=prescription_id
        ).first() is not None


def test_admin_cannot_mark_prescription_collected_before_ready(
    client, make_role_user
):
    """Even a paid prescription must enter Ready for Collection before Collected."""
    patient = make_role_user("Patient", email="direct.collect.patient@example.com")
    doctor = make_role_user("Doctor", email="direct.collect.doctor@example.com")
    admin = make_role_user("Practice Admin", email="direct.collect.admin@example.com")
    prescription_id = request_approve_and_pay(client, patient, doctor)
    login(client, admin)

    response = client.post(
        f"/api/admin/prescriptions/{prescription_id}/status",
        json={"status": "Collected"},
    )

    assert response.status_code == 400
    assert response.get_json()["ok"] is False
    assert "ready for collection" in response.get_json()["error"].lower()


def test_admin_can_complete_ready_to_collected_workflow(client, app, make_role_user):
    """Practice Admin can progress a paid prescription Ready -> Collected."""
    patient = make_role_user("Patient", email="collected.patient@example.com")
    doctor = make_role_user("Doctor", email="collected.doctor@example.com")
    admin = make_role_user("Practice Admin", email="collected.admin@example.com")
    prescription_id = request_approve_and_pay(client, patient, doctor)
    login(client, admin)

    ready = client.post(
        f"/api/admin/prescriptions/{prescription_id}/status",
        json={"status": "Ready for Collection"},
    )
    assert ready.status_code == 200

    collected = client.post(
        f"/api/admin/prescriptions/{prescription_id}/status",
        json={"status": "Collected"},
    )

    assert collected.status_code == 200
    assert collected.get_json()["prescription"]["status"] == "Collected"

    with app.app_context():
        prescription = db.session.get(Prescription, prescription_id)
        assert prescription.status == "Collected"


def test_notification_list_is_isolated_to_logged_in_user(client, app, make_role_user):
    """The notification API must never expose another user's notifications."""
    first = make_role_user("Patient", email="notice.one@example.com")
    second = make_role_user("Patient", email="notice.two@example.com")

    with app.app_context():
        db.session.add(Notification(user_id=first["id"], title="First notice", message="For first user"))
        db.session.add(Notification(user_id=second["id"], title="Second notice", message="For second user"))
        db.session.commit()

    login(client, first)
    response = client.get("/api/notifications")

    assert response.status_code == 200
    titles = {item["title"] for item in response.get_json()["notifications"]}
    assert "First notice" in titles
    assert "Second notice" not in titles


def test_user_can_mark_own_notification_read_and_unread_count_decreases(
    client, app, make_role_user
):
    """Reading an in-app notification must persist read state and update unread count."""
    patient = make_role_user("Patient", email="read.notice@example.com")

    with app.app_context():
        item = Notification(user_id=patient["id"], title="Read me", message="Unread test")
        db.session.add(item)
        db.session.commit()
        notification_id = item.id

    login(client, patient)
    response = client.post(f"/api/notifications/{notification_id}/read")

    assert response.status_code == 200
    body = response.get_json()
    assert body["notification"]["read"] is True
    assert body["unreadCount"] == 0

    with app.app_context():
        stored = db.session.get(Notification, notification_id)
        assert stored.is_read is True


def test_user_cannot_mark_another_users_notification_read(client, app, make_role_user):
    """Notification ownership is enforced when changing read state."""
    owner = make_role_user("Patient", email="notice.owner@example.com")
    other = make_role_user("Patient", email="notice.other@example.com")

    with app.app_context():
        item = Notification(user_id=owner["id"], title="Private notice", message="Owner only")
        db.session.add(item)
        db.session.commit()
        notification_id = item.id

    login(client, other)
    response = client.post(f"/api/notifications/{notification_id}/read")

    assert response.status_code == 404

    with app.app_context():
        stored = db.session.get(Notification, notification_id)
        assert stored.is_read is False
