"""Shared Pytest fixtures for the MediQueue automated test suite."""

import pytest

from app import create_app
from app import email_verification
from app.config import TestConfig
from app.extensions import db
from app.models import PatientProfile, Role, StaffProfile, User


@pytest.fixture()
def app():
    """Create a fresh MediQueue test application and database for each test."""
    test_app = create_app(TestConfig)

    with test_app.app_context():
        db.create_all()

    yield test_app

    with test_app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    """Provide a Flask client that can call routes without starting a server."""
    return app.test_client()


@pytest.fixture()
def runner(app):
    """Provide a runner for testing Flask CLI commands in later chunks."""
    return app.test_cli_runner()


@pytest.fixture()
def make_patient(app):
    """Create a verified-style patient account directly in the isolated test DB.

    Users created by this fixture have no registration OTP record. MediQueue treats
    such pre-existing/seeded patient accounts as already verified, matching the
    application's demo-user behaviour.
    """

    def _make_patient(
        email="patient.test@example.com",
        password="StrongPass123!",
        first_name="Test",
        last_name="Patient",
        active=True,
    ):
        with app.app_context():
            role = Role.query.filter_by(name="Patient").first()
            if role is None:
                role = Role(
                    name="Patient",
                    description="Patient user who can access patient services.",
                )
                db.session.add(role)
                db.session.flush()

            user = User(
                email=email.lower().strip(),
                first_name=first_name,
                last_name=last_name,
                role=role,
                active=active,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()

            db.session.add(
                PatientProfile(
                    user_id=user.id,
                    patient_reference=f"MQP-TEST-{user.id:05d}",
                )
            )
            db.session.commit()

            return {
                "id": user.id,
                "email": user.email,
                "password": password,
            }

    return _make_patient


@pytest.fixture()
def mocked_otp_delivery(monkeypatch):
    """Use a deterministic OTP and replace real email delivery with test doubles.

    This is a *mock*: no SMTP connection is made. The fixture records what the
    application attempted to send so tests can verify the intended behaviour.
    """
    sent = {
        "registration": [],
        "password_reset": [],
    }

    monkeypatch.setattr(email_verification, "generate_otp_code", lambda: "123456")

    def fake_registration_email(user, otp_code, expires_in_minutes=10):
        sent["registration"].append(
            {
                "email": user.email,
                "otp": otp_code,
                "expires_in_minutes": expires_in_minutes,
            }
        )
        return True

    def fake_password_reset_email(user, otp_code, expires_in_minutes=10):
        sent["password_reset"].append(
            {
                "email": user.email,
                "otp": otp_code,
                "expires_in_minutes": expires_in_minutes,
            }
        )
        return True

    monkeypatch.setattr(
        email_verification,
        "send_registration_otp_email",
        fake_registration_email,
    )
    monkeypatch.setattr(
        email_verification,
        "send_password_reset_otp_email",
        fake_password_reset_email,
    )

    return sent


@pytest.fixture()
def make_role_user(app):
    """Create a temporary account for any MediQueue role.

    Patient accounts receive a PatientProfile. Doctor and Nurse accounts receive
    a StaffProfile. Practice Admin accounts need only the core User record.
    Every account exists only inside the isolated test database.
    """

    def _make_role_user(
        role_name,
        email=None,
        password="StrongPass123!",
        first_name="Test",
        last_name="User",
        active=True,
    ):
        allowed_roles = {"Patient", "Doctor", "Nurse", "Practice Admin"}
        if role_name not in allowed_roles:
            raise ValueError(f"Unsupported MediQueue role: {role_name}")

        with app.app_context():
            role = Role.query.filter_by(name=role_name).first()
            if role is None:
                role = Role(
                    name=role_name,
                    description=f"Temporary {role_name} role for automated testing.",
                )
                db.session.add(role)
                db.session.flush()

            safe_role = role_name.lower().replace(" ", ".")
            user_email = (email or f"{safe_role}.test@example.com").lower().strip()

            user = User(
                email=user_email,
                first_name=first_name,
                last_name=last_name,
                role=role,
                active=active,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()

            if role_name == "Patient":
                db.session.add(
                    PatientProfile(
                        user_id=user.id,
                        patient_reference=f"MQP-RBAC-{user.id:05d}",
                    )
                )
            elif role_name in {"Doctor", "Nurse"}:
                db.session.add(
                    StaffProfile(
                        user_id=user.id,
                        job_title=role_name,
                        department="General Practice",
                    )
                )

            db.session.commit()

            return {
                "id": user.id,
                "email": user.email,
                "password": password,
                "role": role_name,
            }

    return _make_role_user
