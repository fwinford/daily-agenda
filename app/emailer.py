"""
Email Module

This module handles sending HTML emails through SMTP servers.
It supports both SSL (port 465) and TLS (port 587) connections
and automatically detects which to use based on the port.

Key features:
- Automatic SSL/TLS detection based on port
- HTML email support
- UTF-8 character encoding
- Secure connection handling
- Works with Gmail, Outlook, and other SMTP providers
"""

import smtplib
import ssl
from email.mime.text import MIMEText

def send_email(host, port, user, password, to_email, subject, html_body):
    """
    Send an HTML email through SMTP with automatic SSL/TLS detection.
    
    This function handles the complexity of SMTP connections by automatically
    choosing the right security protocol based on the port number:
    - Port 465: Uses SSL (Gmail's preferred method)
    - Other ports (587): Uses TLS with STARTTLS
    
    Args:
        host (str): SMTP server hostname (e.g., smtp.gmail.com)
        port (int): SMTP server port (465 for SSL, 587 for TLS)
        user (str): SMTP username (usually your email address)
        password (str): SMTP password (use app passwords, not main password)
        to_email (str): Recipient email address
        subject (str): Email subject line
        html_body (str): HTML content for the email body
        
    Raises:
        smtplib.SMTPException: For authentication or connection errors
        socket.error: For network connectivity issues
    """
    # Create the email message with proper headers
    msg = MIMEText(html_body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_email
    
    # Choose connection method based on port
    if port == 465:
        # SSL connection (Gmail's preferred method)
        # Creates an encrypted connection from the start
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context) as s:
            s.login(user, password)
            s.sendmail(user, [to_email], msg.as_string())
    else:
        # TLS connection (most other providers)
        # Starts unencrypted then upgrades to encrypted with STARTTLS
        with smtplib.SMTP(host, port) as s:
            s.starttls()  # Upgrade to encrypted connection
            s.login(user, password)
            s.sendmail(user, [to_email], msg.as_string())