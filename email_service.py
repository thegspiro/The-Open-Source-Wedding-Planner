import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from html import escape
import os

def send_reminder_email(to_email, couple_names, task_title, task_description, due_date):
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))
    smtp_user = os.environ.get('SMTP_USER')
    smtp_password = os.environ.get('SMTP_PASSWORD')
    from_email = os.environ.get('FROM_EMAIL', smtp_user)

    if not smtp_user or not smtp_password:
        print(f"Email not configured. Would send to {to_email} for: {task_title}")
        return

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Wedding Reminder: {task_title}'
        msg['From'] = from_email
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

        # Escape user-provided data to prevent HTML injection
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

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")
