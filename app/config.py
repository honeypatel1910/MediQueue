import os
from pathlib import Path


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


BASE_DIR = Path(__file__).resolve().parent.parent


def _normalise_database_url(url: str) -> str:
    """Normalise database URLs for SQLAlchemy drivers."""
    if url.startswith("mysql://"):
        return url.replace("mysql://", "mysql+pymysql://", 1)

    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)

    if url.startswith("postgresql://") and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)

    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "mediqueue-secure-secret-change-before-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    WTF_CSRF_TIME_LIMIT = None
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Email / SMTP settings used by registration OTP verification.
    # Real credentials should be stored only in .env, never committed to Git.
    MAIL_SERVER = os.getenv("MAIL_SERVER", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = _env_bool("MAIL_USE_TLS", "true")
    MAIL_USE_SSL = _env_bool("MAIL_USE_SSL", "false")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME or "MediQueue <no-reply@mediqueue.local>")
    MAIL_SUPPRESS_SEND = _env_bool("MAIL_SUPPRESS_SEND", "true")
    EMAIL_OTP_EXPIRY_MINUTES = int(os.getenv("EMAIL_OTP_EXPIRY_MINUTES", "10"))

    # Email copies of in-app notifications. Keep enabled for the feature,
    # but use MAIL_SUPPRESS_SEND=true or MAIL_SEND_NOTIFICATIONS=false in
    # development when SMTP is not configured.
    MAIL_SEND_NOTIFICATIONS = _env_bool("MAIL_SEND_NOTIFICATIONS", "true")
    MAIL_REDIRECT_ALL_TO = os.getenv("MAIL_REDIRECT_ALL_TO", "").strip()

    database_url = os.getenv("DATABASE_URL")

    if database_url:
        SQLALCHEMY_DATABASE_URI = _normalise_database_url(database_url)
    else:
        db_path = Path(os.getenv("SQLITE_DB_PATH", BASE_DIR / "mediqueue.db"))
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"


class TestConfig(Config):
    """Safe, isolated configuration used only by the automated test suite."""

    TESTING = True
    SECRET_KEY = "mediqueue-test-secret-key"
    WTF_CSRF_ENABLED = False

    # Tests use a temporary in-memory SQLite database. The normal PostgreSQL
    # database configured in .env is never opened or modified.
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}

    # Automated tests must never send real registration, password reset,
    # appointment, or prescription emails.
    MAIL_SUPPRESS_SEND = True
    MAIL_SEND_NOTIFICATIONS = False
    MAIL_REDIRECT_ALL_TO = ""