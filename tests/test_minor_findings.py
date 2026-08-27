"""Smaller hardening items from the red-team pass.

R-4  /version fingerprinting
R-6  disabling the RSVP portal does not retire circulated links
R-7  a newline in user text silently kills an outgoing email
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from models import db, User, Wedding, WeddingAccess
from email_service import clean_header, send_reminder_email


# ---------------------------------------------------------------------------
# R-4: version disclosure
# ---------------------------------------------------------------------------

class TestVersionEndpoint:

    def test_version_requires_a_login(self, client, database):
        resp = client.get('/version', follow_redirects=False)
        assert resp.status_code == 302
        assert '/login' in resp.headers.get('Location', '')

    def test_version_available_once_signed_in(self, auth_client):
        client, _ = auth_client
        resp = client.get('/version')
        assert resp.status_code == 200
        assert 'version' in resp.get_json()

    def test_health_stays_public(self, client, database):
        """Uptime monitoring must not need credentials."""
        assert client.get('/health').status_code == 200


# ---------------------------------------------------------------------------
# R-6: RSVP link rotation
# ---------------------------------------------------------------------------

@pytest.fixture
def rsvp_roles(app, database):
    with app.app_context():
        ids = {}
        for role in ('owner', 'planner', 'viewer'):
            u = User(email=f'{role}@example.com', name=role.title(), user_type='self')
            u.set_password('TestPassword1!')
            db.session.add(u)
            db.session.flush()
            ids[f'{role}_id'] = u.id

        wedding = Wedding(
            couple_names='RSVP Couple',
            wedding_date=datetime.utcnow() + timedelta(days=30),
            email='rsvp@example.com',
            rsvp_enabled=True,
            rsvp_token='original-rsvp-token',
        )
        db.session.add(wedding)
        db.session.flush()
        for role in ('owner', 'planner', 'viewer'):
            db.session.add(WeddingAccess(
                user_id=ids[f'{role}_id'], wedding_id=wedding.id, role=role))
        db.session.commit()
        ids['wedding_id'] = wedding.id
        data = dict(ids)

    yield data


def _as(client, user_id):
    with client.session_transaction() as sess:
        sess['user_id'] = user_id
    return client


class TestRsvpLinkRotation:

    def test_regenerating_retires_the_old_link(self, app, client, rsvp_roles):
        _as(client, rsvp_roles['owner_id'])
        client.post(f"/wedding/{rsvp_roles['wedding_id']}/rsvp/regenerate")

        anonymous = app.test_client()
        assert anonymous.get('/rsvp/original-rsvp-token').status_code == 404

    def test_the_new_link_works(self, app, client, rsvp_roles):
        _as(client, rsvp_roles['owner_id'])
        client.post(f"/wedding/{rsvp_roles['wedding_id']}/rsvp/regenerate")

        with app.app_context():
            token = db.session.get(Wedding, rsvp_roles['wedding_id']).rsvp_token
        assert token != 'original-rsvp-token'

        anonymous = app.test_client()
        assert anonymous.get(f'/rsvp/{token}').status_code == 200

    def test_disable_then_enable_still_restores_the_same_link(self, app, client, rsvp_roles):
        """Documents the behaviour R-6 was about: pausing keeps the token.

        This is intentional — the flash message now says so — but it must stay
        deliberate rather than drift, because the couple's mental model of
        "disabled" is that the URL is dead.
        """
        _as(client, rsvp_roles['owner_id'])
        client.post(f"/wedding/{rsvp_roles['wedding_id']}/rsvp/enable")   # disable
        client.post(f"/wedding/{rsvp_roles['wedding_id']}/rsvp/enable")   # re-enable

        with app.app_context():
            w = db.session.get(Wedding, rsvp_roles['wedding_id'])
            assert w.rsvp_enabled is True
            assert w.rsvp_token == 'original-rsvp-token'

    def test_regenerating_after_a_pause_retires_the_old_link(self, app, client, rsvp_roles):
        """The remedy for the above: rotate, and the paused link never comes back."""
        _as(client, rsvp_roles['owner_id'])
        client.post(f"/wedding/{rsvp_roles['wedding_id']}/rsvp/enable")      # disable
        client.post(f"/wedding/{rsvp_roles['wedding_id']}/rsvp/enable")      # re-enable
        client.post(f"/wedding/{rsvp_roles['wedding_id']}/rsvp/regenerate")

        anonymous = app.test_client()
        assert anonymous.get('/rsvp/original-rsvp-token').status_code == 404

    @pytest.mark.parametrize('role', ['planner', 'viewer'])
    def test_only_owners_may_rotate(self, app, client, rsvp_roles, role):
        _as(client, rsvp_roles[f'{role}_id'])
        resp = client.post(f"/wedding/{rsvp_roles['wedding_id']}/rsvp/regenerate")
        assert resp.status_code == 403

        with app.app_context():
            assert db.session.get(Wedding, rsvp_roles['wedding_id']).rsvp_token == 'original-rsvp-token'

    def test_outsider_cannot_rotate(self, app, client, rsvp_roles):
        with app.app_context():
            outsider = User(email='outsider@example.com', name='Outsider', user_type='self')
            outsider.set_password('TestPassword1!')
            db.session.add(outsider)
            db.session.commit()
            outsider_id = outsider.id

        _as(client, outsider_id)
        resp = client.post(f"/wedding/{rsvp_roles['wedding_id']}/rsvp/regenerate")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# R-7: header values built from user text
# ---------------------------------------------------------------------------

class TestCleanHeader:

    @pytest.mark.parametrize('raw,expected', [
        ('Simple Subject', 'Simple Subject'),
        ('With\nnewline', 'With newline'),
        ('With\r\ncrlf', 'With crlf'),
        ('Bcc:\nattacker@evil.com', 'Bcc: attacker@evil.com'),
        ('  padded  ', 'padded'),
        ('tabs\tand\nmixed', 'tabs and mixed'),
        (None, ''),
    ])
    def test_collapses_whitespace(self, raw, expected):
        assert clean_header(raw) == expected

    def test_result_is_always_serializable_as_a_header(self):
        """The property that matters: the message can still be flattened."""
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart('alternative')
        msg['Subject'] = clean_header('Reminder\nBcc: attacker@evil.com')
        msg['To'] = clean_header('guest@example.com')
        msg['From'] = clean_header('couple@example.com')
        msg.attach(MIMEText('body', 'plain'))

        rendered = msg.as_string()  # raises HeaderParseError if injection survived
        assert 'attacker@evil.com' in rendered          # kept as literal text
        assert '\nBcc:' not in rendered                 # but not as a header


class TestReminderEmailSurvivesAwkwardInput:

    @patch('email_service.smtplib.SMTP')
    def test_task_title_with_a_newline_still_sends(self, mock_smtp, monkeypatch):
        """Previously this raised inside send, was swallowed, and sent nothing."""
        monkeypatch.setenv('SMTP_USER', 'user@example.com')
        monkeypatch.setenv('SMTP_PASSWORD', 'secret')

        server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = server

        sent = send_reminder_email(
            to_email='couple@example.com',
            couple_names='Alice & Bob',
            task_title='Book florist\nBcc: attacker@evil.com',
            task_description='Deposit due',
            due_date=datetime.utcnow() + timedelta(days=3),
        )

        assert sent is True
        server.send_message.assert_called_once()
        msg = server.send_message.call_args[0][0]
        assert '\n' not in msg['Subject']
