"""CSRF protection is enforced, and exempt only where it is meant to be.

Until now the suite replaced security.validate_csrf_token with ``lambda: True``
for the whole session, so the validator never executed and nothing here was
covered. conftest.CsrfTestClient now carries a real token instead, which means
every POST in the suite travels the genuine code path — and these tests assert
the path actually refuses the requests it should.

The exempt list is the sharp edge: it is keyed by endpoint *name*, so renaming
a handler silently drops its exemption and starts 403-ing real guests on links
already printed on invitations. The last two tests are there to catch that.
"""

import pytest
from datetime import datetime, timedelta

from app import app as flask_app
from models import db, User, Wedding, WeddingAccess, Guest
from security import CSRF_EXEMPT_ENDPOINTS


# A protected, POST-only endpoint that needs no wedding scaffolding. The CSRF
# check is a before_request hook, so it fires ahead of login_required and the
# response is unambiguous.
PROTECTED_URL = "/logout"


class TestUnsafeRequestsNeedAToken:
    """State-changing requests are refused without a valid token."""

    def test_post_without_a_token_is_refused(self, client):
        response = client.post(PROTECTED_URL, csrf=False)
        assert response.status_code == 403

    def test_post_with_a_forged_token_is_refused(self, client):
        # Give the session a real token, then send a different one.
        client.csrf_token()
        response = client.post(
            PROTECTED_URL,
            csrf=False,
            headers={"X-CSRF-Token": "not-the-session-token"},
        )
        assert response.status_code == 403

    def test_post_with_a_token_but_no_session_token_is_refused(self, client):
        """A token the server never issued is worthless on its own."""
        response = client.post(
            PROTECTED_URL,
            csrf=False,
            headers={"X-CSRF-Token": "a" * 64},
        )
        assert response.status_code == 403

    def test_post_with_the_session_token_in_a_header_is_accepted(self, client):
        response = client.post(PROTECTED_URL)
        assert response.status_code != 403

    def test_post_with_the_session_token_in_a_form_field_is_accepted(self, client):
        """The rendered forms submit the token as a field, not a header."""
        token = client.csrf_token()
        response = client.post(
            PROTECTED_URL,
            csrf=False,
            data={"_csrf_token": token},
        )
        assert response.status_code != 403


class TestSafeRequestsAreUntouched:
    """GET must never be blocked; the check only guards state changes."""

    def test_get_without_a_token_is_allowed(self, client):
        response = client.get("/login")
        assert response.status_code == 200

    def test_get_does_not_require_a_session_token_to_exist(self, client):
        response = client.get("/health")
        assert response.status_code != 403


class TestTheExemptList:
    """The public, link-authenticated surface must stay reachable."""

    @pytest.fixture
    def public_wedding(self, app, database):
        with app.app_context():
            owner = User(email="csrf-owner@example.com", name="Owner",
                         user_type="self")
            owner.set_password("TestPassword1!")
            db.session.add(owner)
            db.session.flush()

            wedding = Wedding(
                couple_names="Public Couple",
                wedding_date=datetime.utcnow() + timedelta(days=60),
                email="csrf-couple@example.com",
                rsvp_enabled=True,
                rsvp_token="csrf-rsvp-token",
            )
            db.session.add(wedding)
            db.session.flush()
            db.session.add(WeddingAccess(user_id=owner.id, wedding_id=wedding.id,
                                         role="owner"))
            db.session.add(Guest(wedding_id=wedding.id, name="Casey Guest",
                                 guest_token="csrf-guest-token"))
            db.session.commit()
        yield {"rsvp_token": "csrf-rsvp-token", "guest_token": "csrf-guest-token"}

    def test_rsvp_submit_works_without_a_token(self, client, public_wedding):
        """Guests arrive from an emailed link with no session and no token."""
        response = client.post(
            f"/rsvp/{public_wedding['rsvp_token']}/submit",
            csrf=False,
            data={"guest_name": "Casey Guest", "rsvp_status": "accepted"},
        )
        assert response.status_code != 403

    def test_checkin_lookup_works_without_a_token(self, client, public_wedding):
        response = client.post(
            f"/checkin/{public_wedding['guest_token']}/lookup",
            csrf=False,
            data={"name": "Casey Guest"},
        )
        assert response.status_code != 403

    def test_every_exempt_endpoint_still_exists(self):
        """A renamed handler drops its exemption without any error.

        That failure is invisible in development — the developer is logged in
        with a token — and shows up as guests being refused by a link that is
        already printed on the invitations.
        """
        registered = {rule.endpoint for rule in flask_app.url_map.iter_rules()}
        missing = CSRF_EXEMPT_ENDPOINTS - registered
        assert not missing, (
            f"CSRF_EXEMPT_ENDPOINTS names endpoints that no longer exist: "
            f"{sorted(missing)}. Renaming a handler silently revokes its "
            f"exemption; update the set in security.py."
        )

    def test_the_exempt_set_is_what_we_think_it_is(self):
        """Pin the list, so widening it has to be a deliberate edit.

        Every name here is a route authenticated by an unguessable token in the
        URL rather than by a session. Anything session-authenticated that ends
        up in this set is a real CSRF hole.
        """
        assert CSRF_EXEMPT_ENDPOINTS == {
            'rsvp_portal', 'rsvp_submit', 'shared_view',
            'guest_identify', 'guest_checkin', 'guest_checkin_lookup',
            'static',
        }
