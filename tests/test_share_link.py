"""Share link lifecycle: create, rotate, revoke.

A share link is a bearer credential handed to people without accounts. Once it
leaks there has to be a way to take it back, and taking it back has to actually
stop the old URL from resolving.
"""

import pytest
from datetime import datetime, timedelta

from models import db, User, Wedding, WeddingAccess


@pytest.fixture
def shared_wedding(app, database):
    """A wedding with an active share link, plus owner/planner/viewer users."""
    with app.app_context():
        users = {}
        for role in ("owner", "planner", "viewer"):
            u = User(email=f"{role}@example.com", name=role.title(), user_type="self")
            u.set_password("TestPassword1!")
            db.session.add(u)
            db.session.flush()
            users[role] = u.id

        wedding = Wedding(
            couple_names="Shared Couple",
            wedding_date=datetime.utcnow() + timedelta(days=45),
            email="shared@example.com",
            share_token="original-share-token",
        )
        db.session.add(wedding)
        db.session.flush()
        for role, uid in users.items():
            db.session.add(WeddingAccess(user_id=uid, wedding_id=wedding.id, role=role))
        db.session.commit()

        data = {"wedding_id": wedding.id, **{f"{r}_id": i for r, i in users.items()}}

    yield data


def _as(client, user_id):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
    return client


class TestRevoke:

    def test_link_works_before_revocation(self, client, shared_wedding):
        resp = client.get("/shared/original-share-token")
        assert resp.status_code == 200

    def test_revoked_link_stops_resolving(self, app, client, shared_wedding):
        _as(client, shared_wedding["owner_id"])
        client.post(f"/wedding/{shared_wedding['wedding_id']}/share/revoke")

        anonymous = app.test_client()
        resp = anonymous.get("/shared/original-share-token")
        assert resp.status_code == 404

    def test_revocation_clears_the_stored_token(self, app, client, shared_wedding):
        _as(client, shared_wedding["owner_id"])
        client.post(f"/wedding/{shared_wedding['wedding_id']}/share/revoke")

        with app.app_context():
            assert db.session.get(Wedding, shared_wedding["wedding_id"]).share_token is None

    def test_revoking_twice_is_harmless(self, client, shared_wedding):
        _as(client, shared_wedding["owner_id"])
        client.post(f"/wedding/{shared_wedding['wedding_id']}/share/revoke")
        resp = client.post(f"/wedding/{shared_wedding['wedding_id']}/share/revoke")
        assert resp.status_code in (200, 302)

    def test_a_new_link_can_be_created_after_revoking(self, app, client, shared_wedding):
        _as(client, shared_wedding["owner_id"])
        client.post(f"/wedding/{shared_wedding['wedding_id']}/share/revoke")
        client.post(f"/wedding/{shared_wedding['wedding_id']}/share/enable")

        with app.app_context():
            token = db.session.get(Wedding, shared_wedding["wedding_id"]).share_token
        assert token
        assert token != "original-share-token"


class TestRegenerate:

    def test_regenerating_replaces_the_token(self, app, client, shared_wedding):
        _as(client, shared_wedding["owner_id"])
        client.post(f"/wedding/{shared_wedding['wedding_id']}/share/regenerate")

        with app.app_context():
            token = db.session.get(Wedding, shared_wedding["wedding_id"]).share_token
        assert token and token != "original-share-token"

    def test_old_link_stops_working_after_regeneration(self, app, client, shared_wedding):
        _as(client, shared_wedding["owner_id"])
        client.post(f"/wedding/{shared_wedding['wedding_id']}/share/regenerate")

        anonymous = app.test_client()
        assert anonymous.get("/shared/original-share-token").status_code == 404

    def test_new_link_works_after_regeneration(self, app, client, shared_wedding):
        _as(client, shared_wedding["owner_id"])
        client.post(f"/wedding/{shared_wedding['wedding_id']}/share/regenerate")

        with app.app_context():
            token = db.session.get(Wedding, shared_wedding["wedding_id"]).share_token

        anonymous = app.test_client()
        assert anonymous.get(f"/shared/{token}").status_code == 200

    def test_enable_does_not_rotate_an_existing_token(self, app, client, shared_wedding):
        """share_enable stays idempotent; rotation is its own explicit action."""
        _as(client, shared_wedding["owner_id"])
        client.post(f"/wedding/{shared_wedding['wedding_id']}/share/enable")

        with app.app_context():
            assert db.session.get(Wedding, shared_wedding["wedding_id"]).share_token == "original-share-token"


class TestAuthorization:
    """Publishing and un-publishing a wedding is an owner decision."""

    @pytest.mark.parametrize("action", ["revoke", "regenerate"])
    def test_planner_cannot_change_the_share_link(self, app, client, shared_wedding, action):
        _as(client, shared_wedding["planner_id"])
        resp = client.post(f"/wedding/{shared_wedding['wedding_id']}/share/{action}")
        assert resp.status_code == 403

        with app.app_context():
            assert db.session.get(Wedding, shared_wedding["wedding_id"]).share_token == "original-share-token"

    @pytest.mark.parametrize("action", ["revoke", "regenerate"])
    def test_viewer_cannot_change_the_share_link(self, app, client, shared_wedding, action):
        _as(client, shared_wedding["viewer_id"])
        resp = client.post(f"/wedding/{shared_wedding['wedding_id']}/share/{action}")
        assert resp.status_code == 403

    @pytest.mark.parametrize("action", ["revoke", "regenerate", "enable"])
    def test_outsider_cannot_change_the_share_link(self, app, client, shared_wedding, action):
        with app.app_context():
            outsider = User(email="outsider@example.com", name="Outsider", user_type="self")
            outsider.set_password("TestPassword1!")
            db.session.add(outsider)
            db.session.commit()
            outsider_id = outsider.id

        _as(client, outsider_id)
        resp = client.post(f"/wedding/{shared_wedding['wedding_id']}/share/{action}")
        assert resp.status_code == 403

    @pytest.mark.parametrize("action", ["revoke", "regenerate"])
    def test_anonymous_cannot_change_the_share_link(self, app, action, shared_wedding):
        anonymous = app.test_client()
        resp = anonymous.post(
            f"/wedding/{shared_wedding['wedding_id']}/share/{action}", follow_redirects=False)
        assert resp.status_code in (302, 401, 403)
        if resp.status_code == 302:
            assert "/login" in resp.headers.get("Location", "")


class TestRevocationIsolation:
    """A NULL token must not become a wildcard that matches other weddings."""

    def test_revoking_one_wedding_does_not_expose_another(self, app, client, shared_wedding):
        with app.app_context():
            other = Wedding(
                couple_names="Other Couple",
                wedding_date=datetime.utcnow() + timedelta(days=45),
                email="other@example.com",
                share_token=None,
            )
            db.session.add(other)
            db.session.commit()

        _as(client, shared_wedding["owner_id"])
        client.post(f"/wedding/{shared_wedding['wedding_id']}/share/revoke")

        anonymous = app.test_client()
        # Neither an empty-ish token nor the revoked one may resolve to anything.
        assert anonymous.get("/shared/original-share-token").status_code == 404
        assert anonymous.get("/shared/None").status_code == 404
        assert anonymous.get("/shared/null").status_code == 404
