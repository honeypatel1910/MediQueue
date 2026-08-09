"""Automated tests for MediQueue registration, login, OTP and password reset."""

from datetime import datetime, timedelta

from app.email_verification import (
    GENERIC_PASSWORD_RESET_MESSAGE,
    OTP_PURPOSE_PASSWORD_RESET,
    OTP_PURPOSE_REGISTRATION,
    OTP_STATUS_EXPIRED,
    OTP_STATUS_PENDING,
    OTP_STATUS_USED,
    OTP_STATUS_VERIFIED,
)
from app.extensions import db
from app.models import EmailVerification, PatientProfile, User


TEST_EMAIL = "new.patient@example.com"
TEST_PASSWORD = "PatientPass123!"
TEST_OTP = "123456"


def registration_payload(**overrides):
    """Return a valid registration request body with optional field overrides."""
    payload = {
        "firstName": "New",
        "lastName": "Patient",
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "confirmPassword": TEST_PASSWORD,
        "phone": "07123456789",
        "address": "1 Test Street",
    }
    payload.update(overrides)
    return payload


def test_registration_rejects_missing_required_fields(client):
    response = client.post(
        "/api/register",
        json={"firstName": "New", "email": TEST_EMAIL},
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "ok": False,
        "error": "First name, last name, email and password are required.",
    }


def test_registration_rejects_short_password(client):
    response = client.post(
        "/api/register",
        json=registration_payload(password="short", confirmPassword="short"),
    )

    assert response.status_code == 400
    assert "at least 8 characters" in response.get_json()["error"]


def test_registration_rejects_password_confirmation_mismatch(client):
    response = client.post(
        "/api/register",
        json=registration_payload(confirmPassword="DifferentPass123!"),
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Password and retype password do not match."


def test_successful_registration_creates_patient_hashes_password_and_creates_otp(
    app,
    client,
    mocked_otp_delivery,
):
    response = client.post("/api/register", json=registration_payload())

    assert response.status_code == 201
    body = response.get_json()
    assert body["ok"] is True
    assert body["email"] == TEST_EMAIL
    assert body["emailVerificationRequired"] is True
    assert body["emailSent"] is True

    assert mocked_otp_delivery["registration"] == [
        {
            "email": TEST_EMAIL,
            "otp": TEST_OTP,
            "expires_in_minutes": 10,
        }
    ]

    with app.app_context():
        user = User.query.filter_by(email=TEST_EMAIL).one()
        assert user.password_hash != TEST_PASSWORD
        assert user.check_password(TEST_PASSWORD) is True
        assert user.has_role("Patient") is True

        profile = PatientProfile.query.filter_by(user_id=user.id).one()
        assert profile.patient_reference == f"MQP-{user.id:05d}"

        otp_record = EmailVerification.query.filter_by(
            user_id=user.id,
            purpose=OTP_PURPOSE_REGISTRATION,
        ).one()
        assert otp_record.status == OTP_STATUS_PENDING
        assert otp_record.otp_hash != TEST_OTP
        assert otp_record.check_otp(TEST_OTP) is True


def test_duplicate_registration_is_rejected(app, client, mocked_otp_delivery):
    first = client.post("/api/register", json=registration_payload())
    second = client.post("/api/register", json=registration_payload())

    assert first.status_code == 201
    assert second.status_code == 400
    assert second.get_json()["error"] == "This email is already registered."

    with app.app_context():
        assert User.query.filter_by(email=TEST_EMAIL).count() == 1


def test_login_is_blocked_until_registration_email_is_verified(
    client,
    mocked_otp_delivery,
):
    registered = client.post("/api/register", json=registration_payload())
    assert registered.status_code == 201

    response = client.post(
        "/api/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )

    assert response.status_code == 403
    body = response.get_json()
    assert body["ok"] is False
    assert body["code"] == "EMAIL_NOT_VERIFIED"
    assert body["email"] == TEST_EMAIL


def test_wrong_registration_otp_is_rejected_and_record_stays_pending(
    app,
    client,
    mocked_otp_delivery,
):
    client.post("/api/register", json=registration_payload())

    response = client.post(
        "/api/verify-email",
        json={"email": TEST_EMAIL, "otp": "999999"},
    )

    assert response.status_code == 400
    assert "Invalid OTP" in response.get_json()["error"]

    with app.app_context():
        record = EmailVerification.query.filter_by(
            email=TEST_EMAIL,
            purpose=OTP_PURPOSE_REGISTRATION,
        ).one()
        assert record.status == OTP_STATUS_PENDING


def test_expired_registration_otp_is_rejected_and_marked_expired(
    app,
    client,
    mocked_otp_delivery,
):
    client.post("/api/register", json=registration_payload())

    with app.app_context():
        record = EmailVerification.query.filter_by(
            email=TEST_EMAIL,
            purpose=OTP_PURPOSE_REGISTRATION,
        ).one()
        record.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.session.commit()

    response = client.post(
        "/api/verify-email",
        json={"email": TEST_EMAIL, "otp": TEST_OTP},
    )

    assert response.status_code == 400
    assert "expired" in response.get_json()["error"].lower()

    with app.app_context():
        record = EmailVerification.query.filter_by(
            email=TEST_EMAIL,
            purpose=OTP_PURPOSE_REGISTRATION,
        ).one()
        assert record.status == OTP_STATUS_EXPIRED


def test_verified_registration_can_login_and_session_contains_patient(
    app,
    client,
    mocked_otp_delivery,
):
    client.post("/api/register", json=registration_payload())

    verification = client.post(
        "/api/verify-email",
        json={"email": TEST_EMAIL, "otp": TEST_OTP},
    )
    assert verification.status_code == 200
    assert verification.get_json()["ok"] is True

    with app.app_context():
        record = EmailVerification.query.filter_by(
            email=TEST_EMAIL,
            purpose=OTP_PURPOSE_REGISTRATION,
        ).one()
        assert record.status == OTP_STATUS_VERIFIED
        assert record.verified_at is not None

    login = client.post(
        "/api/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert login.status_code == 200
    assert login.get_json()["user"]["role"] == "patient"
    assert login.get_json()["user"]["emailVerified"] is True

    session = client.get("/api/session")
    assert session.status_code == 200
    assert session.get_json()["user"]["email"] == TEST_EMAIL


def test_invalid_login_credentials_are_rejected(client, make_patient):
    patient = make_patient()

    response = client.post(
        "/api/login",
        json={"email": patient["email"], "password": "WrongPassword123!"},
    )

    assert response.status_code == 401
    assert response.get_json() == {
        "ok": False,
        "error": "Invalid email/password or inactive account.",
    }


def test_inactive_account_cannot_login(client, make_patient):
    patient = make_patient(
        email="inactive.patient@example.com",
        active=False,
    )

    response = client.post(
        "/api/login",
        json={"email": patient["email"], "password": patient["password"]},
    )

    assert response.status_code == 401
    assert response.get_json()["ok"] is False


def test_logout_clears_authenticated_session(client, make_patient):
    patient = make_patient()

    login = client.post(
        "/api/login",
        json={"email": patient["email"], "password": patient["password"]},
    )
    assert login.status_code == 200
    assert client.get("/api/session").get_json()["user"] is not None

    logout = client.post("/api/logout")
    assert logout.status_code == 200
    assert logout.get_json() == {"ok": True}

    session_after_logout = client.get("/api/session").get_json()
    assert session_after_logout["user"] is None
    assert session_after_logout["unreadCount"] == 0


def test_password_reset_unknown_email_uses_generic_response(
    client,
    mocked_otp_delivery,
):
    response = client.post(
        "/api/password-reset/request",
        json={"email": "unknown@example.com"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["ok"] is True
    assert body["message"] == GENERIC_PASSWORD_RESET_MESSAGE
    assert body["emailSent"] is False
    assert mocked_otp_delivery["password_reset"] == []


def test_password_reset_request_creates_hashed_otp_for_active_user(
    app,
    client,
    make_patient,
    mocked_otp_delivery,
):
    patient = make_patient()

    response = client.post(
        "/api/password-reset/request",
        json={"email": patient["email"]},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["ok"] is True
    assert body["message"] == GENERIC_PASSWORD_RESET_MESSAGE
    assert body["emailSent"] is True

    assert mocked_otp_delivery["password_reset"] == [
        {
            "email": patient["email"],
            "otp": TEST_OTP,
            "expires_in_minutes": 10,
        }
    ]

    with app.app_context():
        record = EmailVerification.query.filter_by(
            user_id=patient["id"],
            purpose=OTP_PURPOSE_PASSWORD_RESET,
        ).one()
        assert record.status == OTP_STATUS_PENDING
        assert record.otp_hash != TEST_OTP
        assert record.check_otp(TEST_OTP) is True


def test_wrong_password_reset_otp_is_rejected(
    client,
    make_patient,
    mocked_otp_delivery,
):
    patient = make_patient()
    client.post(
        "/api/password-reset/request",
        json={"email": patient["email"]},
    )

    response = client.post(
        "/api/password-reset/verify",
        json={"email": patient["email"], "otp": "000000"},
    )

    assert response.status_code == 400
    assert "Invalid OTP" in response.get_json()["error"]


def test_password_cannot_be_changed_before_reset_otp_verification(
    app,
    client,
    make_patient,
    mocked_otp_delivery,
):
    patient = make_patient()
    client.post(
        "/api/password-reset/request",
        json={"email": patient["email"]},
    )

    response = client.post(
        "/api/password-reset/confirm",
        json={
            "email": patient["email"],
            "password": "ChangedPass123!",
            "confirmPassword": "ChangedPass123!",
        },
    )

    assert response.status_code == 400
    assert "verify your password reset OTP" in response.get_json()["error"]

    with app.app_context():
        user = db.session.get(User, patient["id"])
        assert user.check_password(patient["password"]) is True
        assert user.check_password("ChangedPass123!") is False


def test_complete_password_reset_changes_hash_marks_otp_used_and_allows_new_login(
    app,
    client,
    make_patient,
    mocked_otp_delivery,
):
    patient = make_patient()
    old_password = patient["password"]
    new_password = "ChangedPass123!"

    requested = client.post(
        "/api/password-reset/request",
        json={"email": patient["email"]},
    )
    assert requested.status_code == 200

    verified = client.post(
        "/api/password-reset/verify",
        json={"email": patient["email"], "otp": TEST_OTP},
    )
    assert verified.status_code == 200

    confirmed = client.post(
        "/api/password-reset/confirm",
        json={
            "email": patient["email"],
            "password": new_password,
            "confirmPassword": new_password,
        },
    )
    assert confirmed.status_code == 200
    assert confirmed.get_json()["ok"] is True

    with app.app_context():
        user = db.session.get(User, patient["id"])
        assert user.password_hash != new_password
        assert user.check_password(old_password) is False
        assert user.check_password(new_password) is True

        record = EmailVerification.query.filter_by(
            user_id=patient["id"],
            purpose=OTP_PURPOSE_PASSWORD_RESET,
        ).one()
        assert record.status == OTP_STATUS_USED
        assert record.verified_at is not None

    old_login = client.post(
        "/api/login",
        json={"email": patient["email"], "password": old_password},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/login",
        json={"email": patient["email"], "password": new_password},
    )
    assert new_login.status_code == 200
    assert new_login.get_json()["user"]["email"] == patient["email"]
