"""Tests for authentication routes: register, login, logout, and login_required."""

import pytest
from models import db, User


class TestRegister:
    """Tests for the /register route."""

    def test_register_get_returns_200(self, client):
        resp = client.get('/register')
        assert resp.status_code == 200

    def test_register_valid_data_creates_user(self, client):
        resp = client.post('/register', data={
            'name': 'New User',
            'email': 'newuser@example.com',
            'password': 'StrongPass1!',
            'confirm_password': 'StrongPass1!',
            'user_type': 'self',
        }, follow_redirects=False)
        # Successful registration redirects to index
        assert resp.status_code == 302

        # Verify user was created in the database
        with client.application.app_context():
            user = User.query.filter_by(email='newuser@example.com').first()
            assert user is not None
            assert user.name == 'New User'
            assert user.user_type == 'self'

    def test_register_sets_session(self, client):
        client.post('/register', data={
            'name': 'Session User',
            'email': 'session@example.com',
            'password': 'StrongPass1!',
            'confirm_password': 'StrongPass1!',
            'user_type': 'self',
        })
        with client.session_transaction() as sess:
            assert 'user_id' in sess

    def test_register_duplicate_email_fails(self, client, seed_data):
        resp = client.post('/register', data={
            'name': 'Duplicate',
            'email': 'test@example.com',  # already exists via seed_data
            'password': 'StrongPass1!',
            'confirm_password': 'StrongPass1!',
            'user_type': 'self',
        })
        # Should re-render the registration form (200), not redirect
        assert resp.status_code == 200
        assert b'already exists' in resp.data

    def test_register_weak_password_fails(self, client):
        resp = client.post('/register', data={
            'name': 'Weak',
            'email': 'weak@example.com',
            'password': 'short',
            'confirm_password': 'short',
            'user_type': 'self',
        })
        assert resp.status_code == 200
        assert b'Password must be at least 10 characters' in resp.data

    def test_register_password_mismatch_fails(self, client):
        resp = client.post('/register', data={
            'name': 'Mismatch',
            'email': 'mismatch@example.com',
            'password': 'StrongPass1!',
            'confirm_password': 'DifferentPass1!',
            'user_type': 'self',
        })
        assert resp.status_code == 200
        assert b'Passwords do not match' in resp.data

    def test_register_missing_user_type_fails(self, client):
        resp = client.post('/register', data={
            'name': 'No Type',
            'email': 'notype@example.com',
            'password': 'StrongPass1!',
            'confirm_password': 'StrongPass1!',
            'user_type': 'invalid',
        })
        assert resp.status_code == 200
        assert b'Please select how you will use the app' in resp.data


class TestLogin:
    """Tests for the /login route."""

    def test_login_get_returns_200(self, client):
        resp = client.get('/login')
        assert resp.status_code == 200

    def test_login_correct_credentials_succeeds(self, client, seed_data):
        resp = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'TestPassword1!',
        }, follow_redirects=False)
        assert resp.status_code == 302
        with client.session_transaction() as sess:
            assert sess['user_id'] == seed_data['user_id']

    def test_login_wrong_password_fails(self, client, seed_data):
        resp = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'WrongPassword1!',
        })
        assert resp.status_code == 200
        assert b'Invalid email or password' in resp.data

    def test_login_nonexistent_email_fails(self, client):
        resp = client.post('/login', data={
            'email': 'nobody@example.com',
            'password': 'SomePassword1!',
        })
        assert resp.status_code == 200
        assert b'Invalid email or password' in resp.data


class TestLogout:
    """Tests for the /logout route."""

    def test_logout_clears_session(self, auth_client):
        client, seed = auth_client
        # Verify we are logged in
        with client.session_transaction() as sess:
            assert 'user_id' in sess

        # POST, not GET: logout is state-changing, so it must not be reachable
        # from a third-party page's <img> tag.
        resp = client.post('/logout', follow_redirects=False)
        assert resp.status_code == 302
        assert '/login' in resp.headers.get('Location', '')

        with client.session_transaction() as sess:
            assert 'user_id' not in sess


class TestLoginRequired:
    """Tests for the login_required decorator."""

    def test_unauthenticated_user_redirected_to_login(self, client):
        """Accessing a protected route without login should redirect to /login."""
        resp = client.get('/', follow_redirects=False)
        assert resp.status_code == 302
        assert '/login' in resp.headers.get('Location', '')

    def test_settings_requires_login(self, client):
        resp = client.get('/settings', follow_redirects=False)
        assert resp.status_code == 302
        assert '/login' in resp.headers.get('Location', '')
