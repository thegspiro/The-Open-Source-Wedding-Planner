"""Rate limits actually fire, and are scoped the way they claim to be.

conftest clears the limiter's hit counts between tests, because the limiter is
a module-level singleton and would otherwise leak 429s into unrelated tests.
The side effect is that nothing ever reached a limit, so the limited branch,
the abort(429) and the 429 handler were all dead code as far as the suite was
concerned — on the login and public RSVP routes, which is exactly where the
brute-force protection matters.

These tests deliberately spend a whole window.
"""

import pytest
from datetime import datetime, timedelta

from models import db, User, Wedding, WeddingAccess, Guest
from security import RateLimiter


# Mirrors the decorators in app.py. If a limit is retuned, update it here; the
# test asserting these match the real decorators will point you at the drift.
LOGIN_MAX_REQUESTS = 10
REGISTER_MAX_REQUESTS = 10


class TestTheLimiterItself:
    """Unit-level behaviour, with no HTTP in the way."""

    def test_allows_requests_up_to_the_limit(self):
        limiter = RateLimiter()
        for i in range(5):
            is_limited, remaining, _ = limiter.is_rate_limited("k", 5, 60)
            assert is_limited is False, f"refused request {i + 1} of 5"
            assert remaining == 5 - (i + 1)

    def test_refuses_the_request_after_the_limit(self):
        limiter = RateLimiter()
        for _ in range(5):
            limiter.is_rate_limited("k", 5, 60)
        is_limited, remaining, retry_after = limiter.is_rate_limited("k", 5, 60)
        assert is_limited is True
        assert remaining == 0
        assert retry_after > 0, "a refused caller must be told when to retry"

    def test_keys_are_counted_separately(self):
        """One caller burning their budget must not lock out everybody else."""
        limiter = RateLimiter()
        for _ in range(5):
            limiter.is_rate_limited("noisy", 5, 60)
        assert limiter.is_rate_limited("noisy", 5, 60)[0] is True
        assert limiter.is_rate_limited("quiet", 5, 60)[0] is False

    def test_hits_outside_the_window_stop_counting(self):
        """The window slides; it is not a fixed bucket that never drains."""
        limiter = RateLimiter()
        for _ in range(5):
            limiter.is_rate_limited("k", 5, 60)
        assert limiter.is_rate_limited("k", 5, 60)[0] is True

        # Age every recorded hit past the window rather than sleeping for it.
        limiter._hits["k"] = [t - 120 for t in limiter._hits["k"]]
        assert limiter.is_rate_limited("k", 5, 60)[0] is False

    def test_cleanup_drops_keys_with_no_live_hits(self):
        limiter = RateLimiter()
        limiter.is_rate_limited("k", 5, 60)
        limiter._hits["k"] = [t - 7200 for t in limiter._hits["k"]]
        limiter._last_cleanup = 0  # force the periodic cleanup to run
        limiter._cleanup()
        assert "k" not in limiter._hits, "expired keys must not accumulate forever"


class TestMethodScoping:
    """A view that serves a form on GET must be able to count only the POST."""

    def test_uncounted_methods_do_not_consume_the_budget(self, app):
        from security import rate_limit

        calls = []

        @rate_limit(max_requests=2, window_seconds=60, methods=('POST',))
        def view():
            calls.append(1)
            return 'ok'

        with app.test_request_context('/thing', method='GET'):
            for _ in range(10):
                assert view() == 'ok'
        assert len(calls) == 10

    def test_counted_methods_still_hit_the_limit(self, app):
        from werkzeug.exceptions import TooManyRequests
        from security import rate_limit

        @rate_limit(max_requests=2, window_seconds=60, methods=('POST',))
        def view():
            return 'ok'

        with app.test_request_context('/thing', method='POST'):
            assert view() == 'ok'
            assert view() == 'ok'
            with pytest.raises(TooManyRequests):
                view()

    def test_omitting_methods_counts_everything(self, app):
        """GET-only public endpoints rely on this; don't regress it."""
        from werkzeug.exceptions import TooManyRequests
        from security import rate_limit

        @rate_limit(max_requests=2, window_seconds=60)
        def view():
            return 'ok'

        with app.test_request_context('/thing', method='GET'):
            assert view() == 'ok'
            assert view() == 'ok'
            with pytest.raises(TooManyRequests):
                view()


class TestLoginIsRateLimited:
    """Brute-forcing a password has to become expensive."""

    @pytest.fixture
    def registered_user(self, app, database):
        with app.app_context():
            user = User(email="target@example.com", name="Target",
                        user_type="self")
            user.set_password("TestPassword1!")
            db.session.add(user)
            db.session.commit()
        yield {"email": "target@example.com"}

    def _attempt(self, client, email):
        return client.post("/login", data={"email": email,
                                           "password": "WrongPassword1!"})

    def test_repeated_failures_are_eventually_refused(self, client, registered_user):
        email = registered_user["email"]
        for i in range(LOGIN_MAX_REQUESTS):
            response = self._attempt(client, email)
            assert response.status_code != 429, (
                f"attempt {i + 1} was refused, but the limit is "
                f"{LOGIN_MAX_REQUESTS}"
            )

        response = self._attempt(client, email)
        assert response.status_code == 429

    def test_the_refusal_says_how_long_to_wait(self, client, registered_user):
        email = registered_user["email"]
        for _ in range(LOGIN_MAX_REQUESTS + 1):
            response = self._attempt(client, email)
        body = response.get_data(as_text=True)
        assert "Traceback" not in body
        assert "seconds" in body, "a refused caller must be told when to retry"

    def test_viewing_the_login_page_does_not_use_up_the_budget(self, client,
                                                              registered_user):
        """Reloading a form is not a login attempt.

        The limit counted every request to the endpoint, GET included, so a
        visitor who opened the login page eleven times in five minutes was
        locked out of logging in at all.
        """
        for _ in range(LOGIN_MAX_REQUESTS + 5):
            assert client.get("/login").status_code == 200

        response = client.post("/login", data={"email": registered_user["email"],
                                               "password": "TestPassword1!"})
        assert response.status_code != 429

    def test_a_limited_visitor_is_not_bounced_around(self, client, registered_user):
        """The refusal must not redirect into another rate-limited page.

        It used to redirect to index, which redirects an anonymous visitor to
        /login, which is itself rate limited — so the browser bounced between
        the two until it gave up with a redirect loop, and the visitor had no
        idea what had happened.
        """
        email = registered_user["email"]
        for _ in range(LOGIN_MAX_REQUESTS + 1):
            response = self._attempt(client, email)

        assert response.status_code == 429, (
            "the refusal must carry the 429 status so proxies and monitoring "
            "can see it"
        )
        assert "Location" not in response.headers


class TestRegistrationIsRateLimited:
    """Otherwise the account table is a free-for-all."""

    def test_repeated_registrations_are_eventually_refused(self, client, database):
        last = None
        for i in range(REGISTER_MAX_REQUESTS + 1):
            last = client.post("/register", data={
                "email": f"spam{i}@example.com",
                "name": "Spam",
                "password": "TestPassword1!",
                "confirm_password": "TestPassword1!",
                "user_type": "self",
            })
        assert last.status_code == 429


class TestPublicRsvpIsRateLimited:
    """The RSVP link is public; guessing guest names must not be free."""

    @pytest.fixture
    def rsvp_wedding(self, app, database):
        with app.app_context():
            owner = User(email="rl-owner@example.com", name="Owner",
                         user_type="self")
            owner.set_password("TestPassword1!")
            db.session.add(owner)
            db.session.flush()
            wedding = Wedding(
                couple_names="Rate Limited Couple",
                wedding_date=datetime.utcnow() + timedelta(days=60),
                email="rl-couple@example.com",
                rsvp_enabled=True,
                rsvp_token="rl-rsvp-token",
            )
            db.session.add(wedding)
            db.session.flush()
            db.session.add(WeddingAccess(user_id=owner.id,
                                         wedding_id=wedding.id, role="owner"))
            db.session.add(Guest(wedding_id=wedding.id, name="Dana Guest",
                                 guest_token="rl-guest-token"))
            db.session.commit()
        yield {"rsvp_token": "rl-rsvp-token", "guest_token": "rl-guest-token"}

    def test_checkin_lookup_is_eventually_refused(self, client, rsvp_wedding):
        """10 per minute per the decorator: enough for a real guest, not for a
        script walking the guest list."""
        url = f"/checkin/{rsvp_wedding['guest_token']}/lookup"
        last = None
        for i in range(11):
            last = client.post(url, data={"name": f"Guess {i}"})
        assert last.status_code == 429
