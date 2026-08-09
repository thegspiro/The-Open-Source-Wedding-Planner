"""Shared pytest fixtures for the wedding planner test suite."""

import pytest
from datetime import datetime, timedelta

from sqlalchemy.pool import StaticPool

from app import app as flask_app, seed_default_emergency_kit
from models import db as _db, User, Wedding, WeddingAccess


@pytest.fixture(scope="session")
def app():
    """Create a Flask application configured for testing."""
    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        # Every new connection to sqlite:///:memory: gets its own empty database.
        # StaticPool pins the whole app to a single connection so tables created
        # in a fixture are still there when the request handler runs.
        SQLALCHEMY_ENGINE_OPTIONS={
            "poolclass": StaticPool,
            "connect_args": {"check_same_thread": False},
        },
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


def _make_user(email, name, user_type="self"):
    user = User(email=email, name=name, user_type=user_type)
    user.set_password("TestPassword1!")
    _db.session.add(user)
    _db.session.flush()
    return user


@pytest.fixture(scope="function")
def two_tenants(app, database):
    """Two unrelated users, each owning their own wedding.

    Used to prove tenant isolation: the 'outsider' has a valid account but no
    WeddingAccess row for the victim's wedding, so every wedding-scoped route
    must refuse them.
    """
    with app.app_context():
        victim = _make_user("victim@example.com", "Victim")
        outsider = _make_user("outsider@example.com", "Outsider")

        victim_wedding = Wedding(
            couple_names="Victim Couple",
            wedding_date=datetime.utcnow() + timedelta(days=90),
            email="victim-couple@example.com",
        )
        outsider_wedding = Wedding(
            couple_names="Outsider Couple",
            wedding_date=datetime.utcnow() + timedelta(days=90),
            email="outsider-couple@example.com",
        )
        _db.session.add_all([victim_wedding, outsider_wedding])
        _db.session.flush()

        _db.session.add_all([
            WeddingAccess(user_id=victim.id, wedding_id=victim_wedding.id, role="owner"),
            WeddingAccess(user_id=outsider.id, wedding_id=outsider_wedding.id, role="owner"),
        ])
        _db.session.commit()

        yield {
            "victim_id": victim.id,
            "victim_wedding_id": victim_wedding.id,
            "outsider_id": outsider.id,
            "outsider_wedding_id": outsider_wedding.id,
        }


@pytest.fixture(scope="function")
def outsider_client(client, two_tenants):
    """A logged-in client with no access to the victim's wedding."""
    with client.session_transaction() as sess:
        sess["user_id"] = two_tenants["outsider_id"]
    return client, two_tenants


@pytest.fixture(scope="function")
def roles(app, database):
    """One wedding with an owner, a planner, and a viewer collaborator."""
    with app.app_context():
        owner = _make_user("owner@example.com", "Owner")
        planner = _make_user("planner@example.com", "Planner", "professional")
        viewer = _make_user("viewer@example.com", "Viewer")

        wedding = Wedding(
            couple_names="Role Test Couple",
            wedding_date=datetime.utcnow() + timedelta(days=90),
            email="roles@example.com",
        )
        _db.session.add(wedding)
        _db.session.flush()

        _db.session.add_all([
            WeddingAccess(user_id=owner.id, wedding_id=wedding.id, role="owner"),
            WeddingAccess(user_id=planner.id, wedding_id=wedding.id, role="planner"),
            WeddingAccess(user_id=viewer.id, wedding_id=wedding.id, role="viewer"),
        ])
        _db.session.commit()

        yield {
            "wedding_id": wedding.id,
            "owner_id": owner.id,
            "planner_id": planner.id,
            "viewer_id": viewer.id,
        }
