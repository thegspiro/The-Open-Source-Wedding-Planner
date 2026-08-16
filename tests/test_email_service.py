"""Message construction and SMTP handling.

email_service.py had no tests at all. It matters for two reasons beyond
coverage: it interpolates guest-supplied names straight into HTML, and it is
the one module that fails silently by design -- an unconfigured or unreachable
server returns False rather than raising, so a broken mail setup looks exactly
like a working one from the outside.

No network here. smtplib.SMTP is replaced with a recording double, so these
assert what would go on the wire.
"""

import smtplib
import pytest
from datetime import date, datetime

import email_service
from email_service import (_get_smtp_config, _send_message, send_reminder_email,
                           send_guest_email, send_pdf_email)


class FakeSMTP:
    """Stands in for smtplib.SMTP and records what it was asked to do."""

    instances = []

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.started_tls = False
        self.login_args = None
        self.sent = []
        self.quit_called = False
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.quit_called = True
        return False

    def starttls(self):
        self.started_tls = True

    def login(self, user, password):
        self.login_args = (user, password)

    def send_message(self, msg):
        self.sent.append(msg)


class ExplodingSMTP(FakeSMTP):
    def login(self, user, password):
        raise smtplib.SMTPAuthenticationError(535, b"nope")


@pytest.fixture
def smtp(monkeypatch):
    """A configured mail server that records instead of sending."""
    FakeSMTP.instances = []
    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setenv("SMTP_USER", "robot@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "hunter2")
    monkeypatch.setenv("SMTP_HOST", "mail.example.com")
    monkeypatch.setenv("SMTP_PORT", "2525")
    monkeypatch.delenv("FROM_EMAIL", raising=False)
    yield FakeSMTP


@pytest.fixture
def unconfigured(monkeypatch):
    """No credentials, which is the default for a fresh install."""
    FakeSMTP.instances = []
    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    yield FakeSMTP


def only_message(fake):
    assert len(fake.instances) == 1, f"expected one connection, got {len(fake.instances)}"
    server = fake.instances[0]
    assert len(server.sent) == 1
    return server.sent[0]


def body_of(msg, subtype):
    for part in msg.walk():
        if part.get_content_subtype() == subtype:
            return part.get_payload(decode=True).decode("utf-8")
    raise AssertionError(f"no {subtype} part in the message")


class TestConfig:
    def test_defaults_are_used_when_nothing_is_set(self, monkeypatch):
        for var in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD",
                    "FROM_EMAIL"):
            monkeypatch.delenv(var, raising=False)
        cfg = _get_smtp_config()
        assert cfg["host"] == "smtp.gmail.com"
        assert cfg["port"] == 587
        assert cfg["user"] is None

    def test_the_port_is_an_integer(self, monkeypatch):
        """It comes out of the environment as a string; smtplib needs an int."""
        monkeypatch.setenv("SMTP_PORT", "2525")
        assert _get_smtp_config()["port"] == 2525

    def test_from_email_falls_back_to_the_smtp_user(self, monkeypatch):
        monkeypatch.setenv("SMTP_USER", "robot@example.com")
        monkeypatch.delenv("FROM_EMAIL", raising=False)
        assert _get_smtp_config()["from_email"] == "robot@example.com"

    def test_from_email_wins_when_it_is_set(self, monkeypatch):
        monkeypatch.setenv("SMTP_USER", "robot@example.com")
        monkeypatch.setenv("FROM_EMAIL", "hello@ourwedding.example")
        assert _get_smtp_config()["from_email"] == "hello@ourwedding.example"


class TestSending:
    def test_a_configured_server_gets_tls_a_login_and_the_message(self, smtp):
        msg = _build_plain("Subject line", "someone@example.com")
        assert _send_message(msg) is True

        server = smtp.instances[0]
        assert (server.host, server.port) == ("mail.example.com", 2525)
        assert server.started_tls is True, "credentials must not cross in the clear"
        assert server.login_args == ("robot@example.com", "hunter2")
        assert len(server.sent) == 1

    def test_the_from_header_is_set(self, smtp):
        msg = _build_plain("Subject line", "someone@example.com")
        _send_message(msg)
        assert only_message(smtp)["From"] == "robot@example.com"

    def test_an_override_replaces_the_from_address(self, smtp):
        msg = _build_plain("Subject line", "someone@example.com")
        _send_message(msg, from_email_override="planner@example.com")
        assert only_message(smtp)["From"] == "planner@example.com"

    def test_nothing_is_sent_when_mail_is_not_configured(self, unconfigured):
        msg = _build_plain("Subject line", "someone@example.com")
        assert _send_message(msg) is False
        assert unconfigured.instances == [], "connected without credentials"

    def test_a_failing_server_reports_false_rather_than_raising(self, monkeypatch):
        """Callers treat this as best-effort; an outage must not 500 a request."""
        FakeSMTP.instances = []
        monkeypatch.setattr(email_service.smtplib, "SMTP", ExplodingSMTP)
        monkeypatch.setenv("SMTP_USER", "robot@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "hunter2")
        msg = _build_plain("Subject line", "someone@example.com")
        assert _send_message(msg) is False


class TestReminderEmail:
    def test_it_carries_the_task_and_the_date_in_both_parts(self, smtp):
        assert send_reminder_email(
            "couple@example.com", "Alice & Bob", "Book the DJ",
            "Call the venue first", date(2026, 6, 14),
        ) is True

        msg = only_message(smtp)
        assert msg["To"] == "couple@example.com"
        assert "Book the DJ" in msg["Subject"]
        for subtype in ("plain", "html"):
            body = body_of(msg, subtype)
            assert "Book the DJ" in body
            assert "June 14, 2026" in body

    def test_a_task_with_no_description_still_sends(self, smtp):
        assert send_reminder_email("couple@example.com", "Alice & Bob",
                                   "Book the DJ", None, date(2026, 6, 14)) is True
        html = body_of(only_message(smtp), "html")
        assert "Description:" not in html

    def test_markup_in_the_couple_names_is_escaped(self, smtp):
        """Couple names are user input and land in an HTML body."""
        send_reminder_email("couple@example.com", "<script>alert(1)</script>",
                            "Book the DJ", None, date(2026, 6, 14))
        html = body_of(only_message(smtp), "html")
        assert "<script>" not in html
        assert "&lt;script&gt;" in html


class TestGuestEmail:
    def test_the_message_and_the_couple_reach_the_guest(self, smtp):
        assert send_guest_email(
            "guest@example.com", "Casey", "Alice & Bob",
            datetime(2026, 6, 14), "Day-of details", "Doors open at four.",
        ) is True

        msg = only_message(smtp)
        assert msg["Subject"] == "Day-of details"
        assert msg["To"] == "guest@example.com"
        text = body_of(msg, "plain")
        assert "Casey" in text
        assert "Doors open at four." in text
        assert "June 14, 2026" in body_of(msg, "html")

    def test_the_checkin_link_is_included_when_given(self, smtp):
        send_guest_email("guest@example.com", "Casey", "Alice & Bob",
                         datetime(2026, 6, 14), "Details", "See you soon.",
                         guest_link="https://example.com/g/abc123")
        msg = only_message(smtp)
        assert "https://example.com/g/abc123" in body_of(msg, "plain")
        assert 'href="https://example.com/g/abc123"' in body_of(msg, "html")

    def test_no_link_section_when_none_is_given(self, smtp):
        send_guest_email("guest@example.com", "Casey", "Alice & Bob",
                         datetime(2026, 6, 14), "Details", "See you soon.")
        assert "check-in link" not in body_of(only_message(smtp), "plain")

    def test_a_wedding_with_no_date_still_sends(self, smtp):
        assert send_guest_email("guest@example.com", "Casey", "Alice & Bob",
                                None, "Details", "See you soon.") is True

    def test_markup_in_a_guest_name_is_escaped(self, smtp):
        """Guest names arrive from the public RSVP form."""
        send_guest_email("guest@example.com", "<img src=x onerror=alert(1)>",
                         "Alice & Bob", datetime(2026, 6, 14), "Details", "Hi.")
        html = body_of(only_message(smtp), "html")
        assert "<img src=x" not in html
        assert "&lt;img" in html


class TestPdfEmail:
    def test_the_pdf_is_attached_with_its_filename(self, smtp):
        assert send_pdf_email("couple@example.com", "Your timeline",
                              "Attached.", b"%PDF-1.4 fake",
                              "timeline.pdf") is True

        msg = only_message(smtp)
        attachments = [p for p in msg.walk()
                       if p.get_content_type() == "application/pdf"]
        assert len(attachments) == 1
        assert attachments[0].get_filename() == "timeline.pdf"
        assert attachments[0].get_payload(decode=True) == b"%PDF-1.4 fake"

    def test_the_body_text_is_kept(self, smtp):
        send_pdf_email("couple@example.com", "Your timeline", "Attached.",
                       b"%PDF-1.4 fake", "timeline.pdf")
        assert "Attached." in body_of(only_message(smtp), "plain")

    def test_the_sender_can_be_overridden(self, smtp):
        send_pdf_email("vendor@example.com", "Your timeline", "Attached.",
                       b"%PDF-1.4 fake", "timeline.pdf",
                       from_email="couple@ourwedding.example")
        assert only_message(smtp)["From"] == "couple@ourwedding.example"


def _build_plain(subject, to_email):
    from email.mime.text import MIMEText
    msg = MIMEText("body", "plain")
    msg["Subject"] = subject
    msg["To"] = to_email
    return msg
