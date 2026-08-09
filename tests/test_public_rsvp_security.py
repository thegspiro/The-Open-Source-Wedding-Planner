"""Security of the public RSVP and check-in surface.

These routes take no login at all — the only thing between an attacker and a
guest record is an RSVP link that gets printed on invitations and forwarded
through group chats. Treat that link as public and test accordingly.

Each test here corresponds to a step in a reproduced attack chain.
"""

import pytest
from datetime import datetime, timedelta

from models import db, User, Wedding, WeddingAccess, Guest


VICTIM_TOKEN = "victim-guest-token-fixed-for-assertions"


@pytest.fixture
def rsvp_wedding(app, database):
    """A wedding with the RSVP portal open and one guest who has responded."""
    with app.app_context():
        owner = User(email="owner@example.com", name="Owner", user_type="self")
        owner.set_password("TestPassword1!")
        db.session.add(owner)
        db.session.flush()

        wedding = Wedding(
            couple_names="Public Couple",
            wedding_date=datetime.utcnow() + timedelta(days=60),
            email="couple@example.com",
            rsvp_enabled=True,
            rsvp_token="wedding-rsvp-token",
        )
        db.session.add(wedding)
        db.session.flush()
        db.session.add(WeddingAccess(user_id=owner.id, wedding_id=wedding.id, role="owner"))

        responded = Guest(
            wedding_id=wedding.id,
            name="Alice Attendee",
            guest_token=VICTIM_TOKEN,
            rsvp_status="accepted",
            rsvp_date=datetime.utcnow().date(),
            dietary_restrictions="Severe peanut allergy",
        )
        # A guest who was invited but has not replied yet
        pending = Guest(wedding_id=wedding.id, name="Bob Pending",
                        guest_token="bob-guest-token")
        db.session.add_all([responded, pending])
        db.session.commit()

        data = {
            "wedding_id": wedding.id,
            "rsvp_token": "wedding-rsvp-token",
            "responded_id": responded.id,
            "pending_id": pending.id,
        }

    # Yield outside the context. If this fixture's session were still current
    # when the request runs, the request would reuse it and serve these objects
    # from its identity map — so a test that flips rsvp_enabled would be reading
    # its own stale copy rather than what the handler sees.
    yield data


def _submit(client, token, **form):
    return client.post(f"/rsvp/{token}/submit", data=form)


class TestPortalDisabledIsEnforced:
    """Closing RSVPs must stop writes, not just change the page."""

    def test_submit_refused_when_portal_disabled(self, app, client, rsvp_wedding):
        with app.app_context():
            w = db.session.get(Wedding, rsvp_wedding["wedding_id"])
            w.rsvp_enabled = False
            db.session.commit()

        resp = _submit(client, rsvp_wedding["rsvp_token"],
                       guest_name="Gatecrasher", rsvp_status="accepted")

        assert resp.status_code == 403
        with app.app_context():
            assert Guest.query.filter_by(name="Gatecrasher").count() == 0

    def test_submit_allowed_when_portal_enabled(self, app, client, rsvp_wedding):
        """The control case — the check must not break normal RSVPs."""
        resp = _submit(client, rsvp_wedding["rsvp_token"],
                       guest_name="Genuine Walkup", rsvp_status="accepted")
        assert resp.status_code == 200
        with app.app_context():
            assert Guest.query.filter_by(name="Genuine Walkup").count() == 1


class TestExistingResponsesCannotBeRewritten:
    """A typed-in name is not proof of identity."""

    def test_cannot_flip_an_existing_rsvp(self, app, client, rsvp_wedding):
        _submit(client, rsvp_wedding["rsvp_token"],
                guest_name="Alice Attendee", rsvp_status="declined")

        with app.app_context():
            alice = db.session.get(Guest, rsvp_wedding["responded_id"])
            assert alice.rsvp_status == "accepted"

    def test_cannot_erase_an_existing_dietary_restriction(self, app, client, rsvp_wedding):
        """The step with real-world consequences: this field reaches the caterer."""
        _submit(client, rsvp_wedding["rsvp_token"],
                guest_name="Alice Attendee", rsvp_status="accepted",
                dietary_restrictions="none")

        with app.app_context():
            alice = db.session.get(Guest, rsvp_wedding["responded_id"])
            assert alice.dietary_restrictions == "Severe peanut allergy"

    def test_invited_guest_may_still_respond_the_first_time(self, app, client, rsvp_wedding):
        """Refusing overwrites must not block a genuine first RSVP."""
        resp = _submit(client, rsvp_wedding["rsvp_token"],
                       guest_name="Bob Pending", rsvp_status="accepted",
                       dietary_restrictions="Vegetarian")
        assert resp.status_code == 200

        with app.app_context():
            bob = db.session.get(Guest, rsvp_wedding["pending_id"])
            assert bob.rsvp_status == "accepted"
            assert bob.dietary_restrictions == "Vegetarian"

    def test_guest_with_their_own_link_may_change_their_mind(self, app, client, rsvp_wedding):
        """Holding the emailed /g/<token> cookie is proof, so updates are allowed."""
        client.set_cookie("guest_%d" % rsvp_wedding["wedding_id"], VICTIM_TOKEN,
                          domain="localhost")

        resp = _submit(client, rsvp_wedding["rsvp_token"],
                       guest_name="Alice Attendee", rsvp_status="declined")
        assert resp.status_code == 200

        with app.app_context():
            alice = db.session.get(Guest, rsvp_wedding["responded_id"])
            assert alice.rsvp_status == "declined"


class TestIdentityTokenIsNotHandedOut:
    """The check-in cookie is a credential; a guessed name must not earn one."""

    def test_rsvp_submit_does_not_leak_token_on_name_match(self, client, rsvp_wedding):
        resp = _submit(client, rsvp_wedding["rsvp_token"],
                       guest_name="Bob Pending", rsvp_status="accepted")
        cookies = resp.headers.getlist("Set-Cookie")
        assert not any("bob-guest-token" in c for c in cookies)

    def test_checkin_lookup_does_not_leak_token(self, client, rsvp_wedding):
        resp = client.post(f"/checkin/{rsvp_wedding['rsvp_token']}/lookup",
                           data={"name": "alice attendee"})
        cookies = resp.headers.getlist("Set-Cookie")
        assert not any(VICTIM_TOKEN in c for c in cookies)

    def test_checkin_lookup_still_shows_the_table(self, client, rsvp_wedding):
        """Removing the cookie must not remove the feature."""
        resp = client.post(f"/checkin/{rsvp_wedding['rsvp_token']}/lookup",
                           data={"name": "alice attendee"})
        assert resp.status_code == 200
        assert b"Alice Attendee" in resp.data

    def test_new_guest_does_receive_their_own_token(self, app, client, rsvp_wedding):
        """A walk-up creating their own record can be remembered — it is theirs."""
        resp = _submit(client, rsvp_wedding["rsvp_token"],
                       guest_name="Fresh Face", rsvp_status="accepted")
        with app.app_context():
            created = Guest.query.filter_by(name="Fresh Face").first()
        cookies = resp.headers.getlist("Set-Cookie")
        assert any(created.guest_token in c for c in cookies)


class TestProxyTrust:
    """Rate limiting is per-client only if the client IP is real."""

    def test_forwarded_header_ignored_by_default(self, app, client, rsvp_wedding):
        """Without TRUST_PROXY the header must not be honoured — it is forgeable."""
        assert not isinstance(app.wsgi_app, __import__(
            "werkzeug.middleware.proxy_fix", fromlist=["ProxyFix"]).ProxyFix)

    def test_proxy_fix_reads_forwarded_for_when_enabled(self):
        """With TRUST_PROXY the real client IP drives the rate-limit key."""
        from werkzeug.middleware.proxy_fix import ProxyFix
        from flask import Flask, request

        probe = Flask(__name__)
        probe.wsgi_app = ProxyFix(probe.wsgi_app, x_for=1, x_proto=1, x_host=1)

        @probe.route("/whoami")
        def whoami():
            return request.remote_addr or "none"

        c = probe.test_client()
        assert c.get("/whoami", headers={"X-Forwarded-For": "203.0.113.9"}).data == b"203.0.113.9"
