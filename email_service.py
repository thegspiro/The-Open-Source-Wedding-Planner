import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from html import escape
import os

logger = logging.getLogger(__name__)


def _get_smtp_config():
    """Return SMTP settings from environment variables."""
    smtp_user = os.environ.get('SMTP_USER')
    smtp_password = os.environ.get('SMTP_PASSWORD')
    return {
        'host': os.environ.get('SMTP_HOST', 'smtp.gmail.com'),
        'port': int(os.environ.get('SMTP_PORT', 587)),
        'user': smtp_user,
        'password': smtp_password,
        'from_email': os.environ.get('FROM_EMAIL', smtp_user),
    }


def _send_message(msg, from_email_override=None):
    """Send a MIMEBase message via SMTP.

    Returns True on success, False if email is not configured or on error.
    """
    cfg = _get_smtp_config()

    from_addr = from_email_override or cfg['from_email']
    if not cfg['user'] or not cfg['password']:
        logger.info("Email not configured. Would send '%s' to %s",
                     msg['Subject'], msg['To'])
        return False

    msg['From'] = from_addr

    try:
        with smtplib.SMTP(cfg['host'], cfg['port']) as server:
            server.starttls()
            server.login(cfg['user'], cfg['password'])
            server.send_message(msg)
        logger.info("Email sent to %s: %s", msg['To'], msg['Subject'])
        return True
    except Exception as e:
        logger.error("Error sending email to %s: %s", msg['To'], e)
        return False


def send_reminder_email(to_email, couple_names, task_title, task_description, due_date):
    """Send a task-deadline reminder to the couple."""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'Wedding Reminder: {task_title}'
    msg['To'] = to_email

    due_str = due_date.strftime('%B %d, %Y')
    desc_line = f"\n{task_description}" if task_description else ''

    text = (
        f"Wedding Task Reminder\n\n"
        f"Hello {couple_names},\n\n"
        f"Task: {task_title}\n"
        f"Due: {due_str}\n"
        f"{desc_line}\n\n"
        f"Best regards,\nWedding Organizer"
    )

    safe_names = escape(couple_names)
    safe_title = escape(task_title)
    safe_desc = escape(task_description) if task_description else ''
    desc_html = f'<p><strong>Description:</strong> {safe_desc}</p>' if safe_desc else ''

    html = (
        f"<html><body>"
        f"<h2>Wedding Task Reminder</h2>"
        f"<p>Hello {safe_names},</p>"
        f"<div style=\"background:#f9f9f9;padding:15px;\">"
        f"<p><strong>Task:</strong> {safe_title}</p>"
        f"<p><strong>Due:</strong> {due_str}</p>"
        f"{desc_html}"
        f"</div></body></html>"
    )

    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    return _send_message(msg)


def send_guest_email(to_email, guest_name, couple_names, wedding_date,
                     subject, message, guest_link=None):
    """Send an email to a guest with an optional personalized check-in link.

    Used for: day-of details, save-the-dates, general communications.
    The guest_link, when clicked, sets a cookie that identifies them at
    venue check-in.
    """
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['To'] = to_email

    safe_guest = escape(guest_name)
    safe_couple = escape(couple_names)
    safe_message = escape(message)
    date_str = wedding_date.strftime('%B %d, %Y') if wedding_date else ''

    link_text = ''
    link_html = ''
    if guest_link:
        safe_link = escape(guest_link)
        link_text = (
            f"\n\nYour personal check-in link:\n{guest_link}\n"
            f"Click this link to save your details. At the venue, "
            f"simply scan the QR code and you'll be shown your table.\n"
        )
        link_html = (
            f'<div style="background:#e8f5e9;padding:15px;border-radius:8px;margin:15px 0;text-align:center;">'
            f'<p style="margin:0 0 8px;color:#666;">Your personal check-in link</p>'
            f'<a href="{safe_link}" style="display:inline-block;background:#2e7d32;color:white;'
            f'padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">'
            f'View My Details</a>'
            f'<p style="margin:8px 0 0;color:#999;font-size:0.85rem;">'
            f'Click to save your info. At the venue, scan the QR code to find your table.</p>'
            f'</div>'
        )

    text = (
        f"Dear {guest_name},\n\n"
        f"{message}\n"
        f"{link_text}\n"
        f"With love,\n{couple_names}\n"
        f"{date_str}"
    )

    html = (
        f"<html><body style=\"font-family:sans-serif;color:#333;\">"
        f"<div style=\"max-width:500px;margin:0 auto;\">"
        f"<h2 style=\"color:#e91e63;\">{safe_couple}</h2>"
        f"<p>Dear {safe_guest},</p>"
        f"<p>{safe_message}</p>"
        f"{link_html}"
        f"<p style=\"margin-top:20px;\">With love,<br><strong>{safe_couple}</strong></p>"
        f"<p style=\"color:#999;font-size:0.85rem;\">{date_str}</p>"
        f"</div></body></html>"
    )

    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    return _send_message(msg)


def send_pdf_email(to_email, subject, body_text, pdf_bytes, pdf_filename, from_email=None):
    """Send an email with a PDF attachment.

    Args:
        to_email: Recipient email address.
        subject: Email subject line.
        body_text: Plain-text body of the email.
        pdf_bytes: The PDF file content as bytes.
        pdf_filename: Filename for the PDF attachment.
        from_email: Optional sender address (defaults to FROM_EMAIL env var).

    Returns:
        True on success, False on failure.
    """
    msg = MIMEMultipart('mixed')
    msg['Subject'] = subject
    msg['To'] = to_email

    msg.attach(MIMEText(body_text, 'plain'))

    pdf_part = MIMEApplication(pdf_bytes, _subtype='pdf')
    pdf_part.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
    msg.attach(pdf_part)

    return _send_message(msg, from_email_override=from_email)
