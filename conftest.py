"""Shared pytest fixtures for the wedding planner test suite."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from app import app as flask_app, seed_default_emergency_kit
from models import db as _db, User, Wedding, WeddingAccess


@pytest.fixture(scope="session")
def app():
    """Create a Flask application configured for testing."""
    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SECRET_KEY="test-secret-key",
        WTF_CSRF_ENABLED=False,
        SERVER_NAME="localhost",
    )
    # Disable CSRF validation during tests by monkey-patching
    import security
    security._original_validate_csrf = security.validate_csrf_token
    security.validate_csrf_token = lambda: True

    yield flask_app


@pytest.fixture(scope="function")
def database(app):
    """Create fresh database tables for each test function."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app, database):
    """A Flask test client with fresh database."""
    return app.test_client()


@pytest.fixture(scope="function")
def seed_data(app, database):
    """Create a test user, wedding, and wedding access record.

    Returns a dict with the created objects and their ids.
    """
    with app.app_context():
        user = User(
            email="test@example.com",
            name="Test User",
            user_type="self",
        )
        user.set_password("TestPassword1!")
        _db.session.add(user)
        _db.session.flush()

        wedding = Wedding(
            couple_names="Alice & Bob",
            wedding_date=datetime.utcnow() + timedelta(days=90),
            email="couple@example.com",
        )
        _db.session.add(wedding)
        _db.session.flush()

        access = WeddingAccess(
            user_id=user.id,
            wedding_id=wedding.id,
            role="owner",
        )
        _db.session.add(access)
        _db.session.commit()

        data = {
            "user": user,
            "user_id": user.id,
            "wedding": wedding,
            "wedding_id": wedding.id,
        }
        yield data


@pytest.fixture(scope="function")
def auth_client(app, client, seed_data):
    """A test client that is already logged in as the test user."""
    with client.session_transaction() as sess:
        sess["user_id"] = seed_data["user_id"]
    return client, seed_data
