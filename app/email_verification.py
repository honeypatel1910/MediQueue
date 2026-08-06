from datetime import datetime, timedelta
from secrets import randbelow

from flask import current_app

from app.email_service import send_password_reset_otp_email, send_registration_otp_email
from app.extensions import db
from app.models import EmailVerification, User

OTP_PURPOSE_REGISTRATION = "registration"
OTP_PURPOSE_PASSWORD_RESET = "password_reset"
OTP_STATUS_PENDING = "Pending"
OTP_STATUS_VERIFIED = "Verified"
OTP_STATUS_REPLACED = "Replaced"
OTP_STATUS_EXPIRED = "Expired"
OTP_STATUS_USED = "Used"

GENERIC_PASSWORD_RESET_MESSAGE = (
    "If an active account exists for this email address, a password reset OTP has been sent."
)


def generate_otp_code():
    """Return a zero-padded six-digit OTP."""
    return f"{randbelow(1_000_000):06d}"


def latest_verification(user, purpose):
    """Return the latest OTP record for a user and purpose."""
    if user is None:
        return None
    return (
        EmailVerification.query.filter_by(user_id=user.id, purpose=purpose)
        .order_by(EmailVerification.created_at.desc())
        .first()
    )


def latest_registration_verification(user):
    """Return the latest registration OTP record for the user, if any."""
    return latest_verification(user, OTP_PURPOSE_REGISTRATION)


def latest_password_reset_verification(user):
    """Return the latest password reset OTP record for the user, if any."""
    return latest_verification(user, OTP_PURPOSE_PASSWORD_RESET)


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


def _replace_pending_otps(user, purpose):
    pending_records = EmailVerification.query.filter_by(
        user_id=user.id,
        purpose=purpose,
        status=OTP_STATUS_PENDING,
    ).all()
    for record in pending_records:
        record.status = OTP_STATUS_REPLACED


def _issue_otp(user, purpose):
    expiry_minutes = int(current_app.config.get("EMAIL_OTP_EXPIRY_MINUTES", 10))
    otp_code = generate_otp_code()

    _replace_pending_otps(user, purpose)

    verification = EmailVerification(
        user_id=user.id,
        email=user.email,
        purpose=purpose,
        status=OTP_STATUS_PENDING,
        expires_at=datetime.utcnow() + timedelta(minutes=expiry_minutes),
    )
    verification.set_otp(otp_code)
    db.session.add(verification)
    db.session.flush()
    return verification, otp_code, expiry_minutes


def issue_registration_otp(user):
    """Create a fresh registration OTP record and email it to the patient."""
    verification, otp_code, expiry_minutes = _issue_otp(user, OTP_PURPOSE_REGISTRATION)
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


def issue_password_reset_otp(email):
    """Generate a password reset OTP for an active account.

    The user-facing response remains generic so the app does not reveal
    whether a particular email address is registered.
    """
    email = (email or "").lower().strip()
    if not email:
        return False, "Email address is required.", False, None

    user = User.query.filter_by(email=email).first()
    if user is None or not user.is_active:
        return True, GENERIC_PASSWORD_RESET_MESSAGE, False, None

    _, otp_code, expiry_minutes = _issue_otp(user, OTP_PURPOSE_PASSWORD_RESET)
    email_sent = send_password_reset_otp_email(user, otp_code, expiry_minutes)
    return True, GENERIC_PASSWORD_RESET_MESSAGE, email_sent, user


def verify_password_reset_otp(email, otp_code):
    """Verify a password reset OTP before allowing password replacement."""
    email = (email or "").lower().strip()
    otp_code = (otp_code or "").strip()

    if not email or not otp_code:
        return False, "Email address and OTP are required.", None

    user = User.query.filter_by(email=email).first()
    if user is None or not user.is_active:
        return False, "Invalid or expired password reset OTP.", None

    record = latest_password_reset_verification(user)
    if record is None or record.status != OTP_STATUS_PENDING:
        return False, "Please request a new password reset OTP.", user

    if record.is_expired:
        record.status = OTP_STATUS_EXPIRED
        db.session.flush()
        return False, "Password reset OTP expired. Please request a new OTP.", user

    if not record.check_otp(otp_code):
        return False, "Invalid OTP. Please check the code and try again.", user

    record.status = OTP_STATUS_VERIFIED
    record.verified_at = datetime.utcnow()
    db.session.flush()
    return True, "OTP verified. You can now set a new password.", user


def reset_password_after_otp(email, new_password, confirm_password):
    """Set a new password after a verified password reset OTP."""
    email = (email or "").lower().strip()
    new_password = new_password or ""
    confirm_password = confirm_password or ""

    if not email:
        return False, "Email address is required.", None

    if len(new_password) < 8:
        return False, "New password must be at least 8 characters long.", None

    if new_password != confirm_password:
        return False, "New password and retype password do not match.", None

    user = User.query.filter_by(email=email).first()
    if user is None or not user.is_active:
        return False, "Password reset could not be completed. Please request a new OTP.", None

    record = latest_password_reset_verification(user)
    if record is None or record.status != OTP_STATUS_VERIFIED:
        return False, "Please verify your password reset OTP before setting a new password.", user

    if record.is_expired:
        record.status = OTP_STATUS_EXPIRED
        db.session.flush()
        return False, "Password reset OTP expired. Please request a new OTP.", user

    user.set_password(new_password)
    record.status = OTP_STATUS_USED
    record.verified_at = record.verified_at or datetime.utcnow()
    db.session.flush()
    return True, "Password reset successfully. You can now sign in with your new password.", user
