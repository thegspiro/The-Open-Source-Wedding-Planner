import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
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
        
        text = f"""Wedding Task Reminder\n\nHello {couple_names},\n\nTask: {task_title}\nDue: {due_date.strftime('%B %d, %Y')}\n{task_description if task_description else ''}\n\nBest regards,\nWedding Organizer"""
        
        html = f"""<html><body><h2>Wedding Task Reminder</h2><p>Hello {couple_names},</p><div style="background:#f9f9f9;padding:15px;"><p><strong>Task:</strong> {task_title}</p><p><strong>Due:</strong> {due_date.strftime('%B %d, %Y')}</p>{f'<p><strong>Description:</strong> {task_description}</p>' if task_description else ''}</div></body></html>"""
        
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")
