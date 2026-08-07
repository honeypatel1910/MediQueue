"""Shared Pytest fixtures for the MediQueue automated test suite."""

import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db


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
