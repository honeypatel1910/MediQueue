import os
from pathlib import Path

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

    database_url = os.getenv("DATABASE_URL")

    if database_url:
        SQLALCHEMY_DATABASE_URI = _normalise_database_url(database_url)
    else:
        db_path = Path(os.getenv("SQLITE_DB_PATH", BASE_DIR / "mediqueue.db"))
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"