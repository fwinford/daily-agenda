import smtplib
from email.mime.text import MIMEText

def send_email(host, port, user, password, to_email, subject, html_body):
    """Simple SMTP sender with STARTTLS + login."""
    msg = MIMEText(html_body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_email
    with smtplib.SMTP(host, port) as s:
        s.starttls()
        s.login(user, password)
        s.sendmail(user, [to_email], msg.as_string())