from datetime import datetime, timedelta
from secrets import randbelow

from flask import current_app

from app.email_service import send_registration_otp_email
from app.extensions import db
from app.models import EmailVerification, Role, User

OTP_PURPOSE_REGISTRATION = "registration"
OTP_STATUS_PENDING = "Pending"
OTP_STATUS_VERIFIED = "Verified"
OTP_STATUS_REPLACED = "Replaced"
OTP_STATUS_EXPIRED = "Expired"


def generate_otp_code():
    """Return a zero-padded six-digit OTP."""
    return f"{randbelow(1_000_000):06d}"


def latest_registration_verification(user):
    """Return the latest email verification record for the user, if any."""
    if user is None:
        return None
    return (
        EmailVerification.query.filter_by(user_id=user.id, purpose=OTP_PURPOSE_REGISTRATION)
        .order_by(EmailVerification.created_at.desc())
        .first()
    )


def email_is_verified(user):
    """Return whether the user's email should be treated as verified.

    Existing demo/seeded users from earlier chunks do not have OTP records.
    They are treated as already verified so current demo logins keep working.
    New patient registrations create a Pending OTP record and are blocked
    until that record becomes Verified.
    """
    if user is None:
        return False

    if not user.has_role("Patient"):
        return True

    record = latest_registration_verification(user)
    if record is None:
        return True

    return record.status == OTP_STATUS_VERIFIED


def issue_registration_otp(user):
    """Create a fresh OTP record and email it to the patient."""
    expiry_minutes = int(current_app.config.get("EMAIL_OTP_EXPIRY_MINUTES", 10))
    otp_code = generate_otp_code()

    pending_records = EmailVerification.query.filter_by(
        user_id=user.id,
        purpose=OTP_PURPOSE_REGISTRATION,
        status=OTP_STATUS_PENDING,
    ).all()
    for record in pending_records:
        record.status = OTP_STATUS_REPLACED

    verification = EmailVerification(
        user_id=user.id,
        email=user.email,
        purpose=OTP_PURPOSE_REGISTRATION,
        status=OTP_STATUS_PENDING,
        expires_at=datetime.utcnow() + timedelta(minutes=expiry_minutes),
    )
    verification.set_otp(otp_code)
    db.session.add(verification)
    db.session.flush()

    email_sent = send_registration_otp_email(user, otp_code, expiry_minutes)
    return verification, email_sent


def verify_registration_otp(email, otp_code):
    """Verify a patient's registration OTP."""
    email = (email or "").lower().strip()
    otp_code = (otp_code or "").strip()

    if not email or not otp_code:
        return False, "Email address and OTP are required.", None

    user = User.query.filter_by(email=email).first()
    if user is None:
        return False, "No account was found for this email address.", None

    if not user.has_role("Patient"):
        return False, "Only patient registration requires email OTP verification.", user

    record = latest_registration_verification(user)
    if record is None:
        return True, "Email is already verified.", user

    if record.status == OTP_STATUS_VERIFIED:
        return True, "Email is already verified.", user

    if record.status != OTP_STATUS_PENDING:
        return False, "Please request a new OTP and try again.", user

    if record.is_expired:
        record.status = OTP_STATUS_EXPIRED
        db.session.flush()
        return False, "OTP expired. Please request a new OTP.", user

    if not record.check_otp(otp_code):
        return False, "Invalid OTP. Please check the code and try again.", user

    record.status = OTP_STATUS_VERIFIED
    record.verified_at = datetime.utcnow()
    db.session.flush()
    return True, "Email verified successfully. You can now sign in.", user


def resend_registration_otp(email):
    """Generate and email a new OTP for an unverified patient account."""
    email = (email or "").lower().strip()
    if not email:
        return False, "Email address is required.", False, None

    user = User.query.filter_by(email=email).first()
    if user is None:
        return False, "No account was found for this email address.", False, None

    if not user.has_role("Patient"):
        return False, "Only patient accounts can request registration OTP verification.", False, user

    if email_is_verified(user):
        return True, "Email is already verified. You can sign in.", False, user

    _, email_sent = issue_registration_otp(user)
    return True, "A new OTP has been generated and sent to your registered email address.", email_sent, user
