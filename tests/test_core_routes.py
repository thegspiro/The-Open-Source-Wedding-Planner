"""Tests for core routes: index, dashboard, create wedding, and health check."""

import pytest
from unittest.mock import patch
from models import db, Wedding, WeddingAccess, EmergencyKitItem, Person


# ---------------------------------------------------------------------------
# Patch helper (same pattern as existing tests)
# ---------------------------------------------------------------------------

def _patched_get_wedding(wedding_id):
    from flask import g, abort
    wedding = db.session.get(Wedding, wedding_id)
    if wedding is None:
        abort(404)
    user = g.get("user")
    if not user:
        abort(401)
    access = WeddingAccess.query.filter_by(
        user_id=user.id, wedding_id=wedding_id
    ).first()
    if not access:
        abort(403, description="You do not have access to this wedding.")
    g.wedding_role = access.role
    return wedding


class TestHealthCheck:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self, client):
        resp = client.get('/health')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'healthy'
        assert data['database'] == 'connected'


class TestIndex:
    """Tests for the / route."""

    def test_index_redirects_unauthenticated(self, client):
        resp = client.get('/', follow_redirects=False)
        assert resp.status_code == 302
        assert '/login' in resp.headers.get('Location', '')

    def test_index_returns_200_for_authenticated_user(self, auth_client):
        client, seed = auth_client
        resp = client.get('/', follow_redirects=True)
        assert resp.status_code == 200


class TestDashboard:
    """Tests for the /wedding/<id> dashboard route."""

    @patch("app.get_wedding_or_403", side_effect=_patched_get_wedding)
    def test_dashboard_returns_200_for_auth_user(self, mock_gw, auth_client):
        client, seed = auth_client
        resp = client.get(f'/wedding/{seed["wedding_id"]}')
        assert resp.status_code == 200

    def test_dashboard_redirects_unauthenticated(self, client, seed_data):
        resp = client.get(f'/wedding/{seed_data["wedding_id"]}', follow_redirects=False)
        assert resp.status_code == 302
        assert '/login' in resp.headers.get('Location', '')


class TestCreateWedding:
    """Tests for the /wedding/new route."""

    def test_create_wedding_get_requires_login(self, client):
        resp = client.get('/wedding/new', follow_redirects=False)
        assert resp.status_code == 302
        assert '/login' in resp.headers.get('Location', '')

    def test_create_wedding_post_creates_wedding_and_seeds_kit(self, app, client, database):
        """POST to /wedding/new should create a wedding, grant owner access,
        and seed the default emergency kit."""
        with app.app_context():
            from models import User
            user = User(
                email='creator@example.com',
                name='Creator',
                user_type='professional',
            )
            user.set_password('StrongPass1!')
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        # Log in as the new user
        with client.session_transaction() as sess:
            sess['user_id'] = user_id

        resp = client.post('/wedding/new', data={
            'num_people': '2',
            'person_0_name': 'Jane',
            'person_1_name': 'Joe',
            'wedding_date': '2026-09-15',
            'email': 'jane.joe@example.com',
        }, follow_redirects=False)

        # Should redirect to onboarding step2
        assert resp.status_code == 302

        # Verify the wedding was created with owner access and emergency kit seeded
        with app.app_context():
            wedding = Wedding.query.filter_by(couple_names='Jane & Joe').first()
            assert wedding is not None
            assert wedding.email == 'jane.joe@example.com'

            # Verify Person records were created at wedding creation
            people = Person.query.filter_by(wedding_id=wedding.id).order_by(Person.display_order).all()
            assert len(people) == 2
            assert people[0].name == 'Jane'
            assert people[1].name == 'Joe'

            access = WeddingAccess.query.filter_by(
                user_id=user_id, wedding_id=wedding.id
            ).first()
            assert access is not None
            assert access.role == 'owner'

            kit_count = EmergencyKitItem.query.filter_by(wedding_id=wedding.id).count()
            assert kit_count > 0, "Emergency kit should be seeded on wedding creation"
