"""Session lifecycle, password rotation, and redirect safety.

Covers the three gaps that only mattered in combination: a session identifier
that survived login, a lifetime setting that was never applied, and no way for
a user to rotate their own credential.
"""

import pytest

from models import db, User


def _register(client, **overrides):
    form = {
        "name": "New User",
        "email": "new@example.com",
        "password": "StrongPass1!",
        "confirm_password": "StrongPass1!",
        "user_type": "self",
    }
    form.update(overrides)
    return client.post("/register", data=form, follow_redirects=False)


class TestSessionRotation:
    """A session identifier present before login must not become the authenticated one."""

    def test_login_clears_pre_existing_session_contents(self, client, seed_data):
        with client.session_transaction() as sess:
            sess["planted"] = "attacker-value"

        client.post("/login", data={"email": "test@example.com",
                                    "password": "TestPassword1!"})

        with client.session_transaction() as sess:
            assert sess.get("user_id") == seed_data["user_id"]
            assert "planted" not in sess, "login reused the pre-auth session"

    def test_register_clears_pre_existing_session_contents(self, client, database):
        with client.session_transaction() as sess:
            sess["planted"] = "attacker-value"

        _register(client)

        with client.session_transaction() as sess:
            assert sess.get("user_id") is not None
            assert "planted" not in sess

    def test_session_is_permanent_so_lifetime_applies(self, client, seed_data):
        """PERMANENT_SESSION_LIFETIME is only honoured for permanent sessions."""
        client.post("/login", data={"email": "test@example.com",
                                    "password": "TestPassword1!"})
        with client.session_transaction() as sess:
            assert sess.permanent is True


class TestLogout:

    def test_logout_discards_everything_except_the_farewell_flash(self, client, seed_data):
        """Logout must drop the CSRF token and any other carried state, not just user_id.

        The logout flash message is written after the clear, so _flashes coming
        back is expected — anything else surviving is not.
        """
        client.post("/login", data={"email": "test@example.com",
                                    "password": "TestPassword1!"})
        with client.session_transaction() as sess:
            sess["carried_over"] = "should not survive"
            sess["_csrf_token"] = "old-token"

        client.post("/logout")

        with client.session_transaction() as sess:
            assert "user_id" not in sess
            assert set(sess.keys()) <= {"_flashes"}, (
                f"logout left session keys behind: {sorted(sess.keys())}")

    def test_logout_rejects_get(self, client, seed_data):
        """A GET logout can be triggered by any third-party page."""
        resp = client.get("/logout")
        assert resp.status_code == 405


class TestChangePassword:

    def _login(self, client):
        return client.post("/login", data={"email": "test@example.com",
                                           "password": "TestPassword1!"})

    def test_requires_the_current_password(self, app, client, seed_data):
        self._login(client)
        client.post("/password", data={
            "current_password": "WrongPassword1!",
            "new_password": "BrandNewPass9!",
            "confirm_password": "BrandNewPass9!"})

        with app.app_context():
            user = db.session.get(User, seed_data["user_id"])
            assert user.check_password("TestPassword1!")
            assert not user.check_password("BrandNewPass9!")

    def test_enforces_password_strength(self, app, client, seed_data):
        self._login(client)
        client.post("/password", data={
            "current_password": "TestPassword1!",
            "new_password": "weak",
            "confirm_password": "weak"})

        with app.app_context():
            assert db.session.get(User, seed_data["user_id"]).check_password("TestPassword1!")

    def test_requires_matching_confirmation(self, app, client, seed_data):
        self._login(client)
        client.post("/password", data={
            "current_password": "TestPassword1!",
            "new_password": "BrandNewPass9!",
            "confirm_password": "DifferentPass9!"})

        with app.app_context():
            assert db.session.get(User, seed_data["user_id"]).check_password("TestPassword1!")

    def test_changes_the_password(self, app, client, seed_data):
        self._login(client)
        client.post("/password", data={
            "current_password": "TestPassword1!",
            "new_password": "BrandNewPass9!",
            "confirm_password": "BrandNewPass9!"})

        with app.app_context():
            user = db.session.get(User, seed_data["user_id"])
            assert user.check_password("BrandNewPass9!")
            assert not user.check_password("TestPassword1!")

    def test_requires_a_login(self, client, seed_data):
        resp = client.post("/password", data={
            "current_password": "TestPassword1!",
            "new_password": "BrandNewPass9!",
            "confirm_password": "BrandNewPass9!"}, follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers.get("Location", "")


class TestRegistrationEmailValidation:

    @pytest.mark.parametrize("bad", ["notanemail", "no@tld", "@example.com", "spaces here@x.com"])
    def test_rejects_malformed_addresses(self, app, client, database, bad):
        _register(client, email=bad)
        with app.app_context():
            assert User.query.filter_by(email=bad).count() == 0

    def test_accepts_a_valid_address(self, app, client, database):
        _register(client, email="valid.person@example.co.uk")
        with app.app_context():
            assert User.query.filter_by(email="valid.person@example.co.uk").count() == 1


class TestSafeRedirect:
    """Referer is attacker-controlled and must not steer a redirect off-site."""

    def test_offsite_referer_is_ignored(self, client, seed_data):
        with client.session_transaction() as sess:
            sess["user_id"] = seed_data["user_id"]

        resp = client.post(
            f"/wedding/{seed_data['wedding_id']}/comment/add",
            data={"entity_type": "task", "entity_id": "1", "content": "hi"},
            headers={"Referer": "https://evil.example.com/phish"},
            follow_redirects=False)

        location = resp.headers.get("Location", "")
        assert "evil.example.com" not in location

    def test_same_host_referer_is_honoured(self, client, seed_data):
        with client.session_transaction() as sess:
            sess["user_id"] = seed_data["user_id"]

        own_page = f"http://localhost/wedding/{seed_data['wedding_id']}/tasks"
        resp = client.post(
            f"/wedding/{seed_data['wedding_id']}/comment/add",
            data={"entity_type": "task", "entity_id": "1", "content": "hi"},
            headers={"Referer": own_page},
            follow_redirects=False)

        assert resp.headers.get("Location", "") == own_page

    def test_relative_referer_is_honoured(self, client, seed_data):
        with client.session_transaction() as sess:
            sess["user_id"] = seed_data["user_id"]

        resp = client.post(
            f"/wedding/{seed_data['wedding_id']}/comment/add",
            data={"entity_type": "task", "entity_id": "1", "content": "hi"},
            headers={"Referer": "/wedding/1/tasks"},
            follow_redirects=False)

        assert resp.headers.get("Location", "").endswith("/wedding/1/tasks")


class TestHealthEndpoint:

    def test_healthy_response_shape(self, client, database):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.get_json() == {"status": "healthy", "database": "connected"}

    def test_failure_does_not_leak_the_exception(self, client, database, monkeypatch):
        """SQLAlchemy connection errors quote the DSN, which can carry a password."""
        import app as app_module

        def boom(*args, **kwargs):
            raise RuntimeError(
                "connection failed: postgresql://admin:hunter2@db.internal:5432/wedding")

        monkeypatch.setattr(app_module.db.session, "execute", boom)

        resp = client.get("/health")
        assert resp.status_code == 503
        body = resp.get_data(as_text=True)
        assert "hunter2" not in body
        assert "db.internal" not in body
        assert resp.get_json() == {"status": "unhealthy", "database": "disconnected"}
