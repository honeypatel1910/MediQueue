"""Tests for the isolated database used by the automated test suite."""

from sqlalchemy import inspect

from app.extensions import db


def test_database_tables_are_created(app):
    expected_tables = {
        "appointments",
        "appointment_slots",
        "audit_logs",
        "availability_blocks",
        "email_verifications",
        "notifications",
        "patients",
        "prescriptions",
        "professional_registers",
        "roles",
        "staff_profiles",
        "users",
    }

    with app.app_context():
        created_tables = set(inspect(db.engine).get_table_names())

    assert expected_tables.issubset(created_tables)
    assert app.config["TESTING"] is True
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"
    assert app.config["MAIL_SUPPRESS_SEND"] is True
