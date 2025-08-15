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

import os
import smtplib
import ssl
from contextlib import contextmanager
from email.message import EmailMessage
from typing import Iterable, Optional, List
from email.mime.text import MIMEText

SMTP_TIMEOUT = float(os.getenv("SMTP_TIMEOUT", "20"))
SMTP_DEBUG = int(os.getenv("SMTP_DEBUG", "0"))  # 0/1

@contextmanager
def smtp_session(
    host: str,
    port: int,
    username: Optional[str] = None,
    password: Optional[str] = None,
    *,
    use_ssl: bool = False,
    use_tls: bool = True,
    timeout: float = SMTP_TIMEOUT,
):
    """
    Open one SMTP connection (SSL or STARTTLS), log in once, yield the live server.
    Uses smtplib's own context manager so tests that patch __enter__/__exit__ see calls.
    """
    cm = smtplib.SMTP_SSL(host, port, timeout=timeout) if use_ssl else smtplib.SMTP(host, port, timeout=timeout)
    # IMPORTANT: use smtplib's own context manager (tests depend on this)
    with cm as server:
        if SMTP_DEBUG:
            server.set_debuglevel(1)
        server.ehlo()
        if use_tls and not use_ssl:
            ctx = ssl.create_default_context()
            server.starttls(context=ctx)
            server.ehlo()
        if username and password:
            server.login(username, password)
        # yield live server; cleanup handled by smtplib context manager
        yield server

def _send_bulk_raw_auto(
    host: str,
    port: int,
    username: Optional[str],
    password: Optional[str],
    payloads: Iterable[tuple[str, Iterable[str], str]],
) -> int:
    """
    Bulk-sends raw MIME strings using sendmail(), reusing a single SMTP connection.
    Each payload is (from_addr, to_addrs, raw_message_string).
    Port 465 => implicit SSL, otherwise STARTTLS.
    """
    try:
        p = int(port)
    except Exception:
        p = 587

    use_ssl = (p == 465)
    sent = 0
    with smtp_session(host, p, username, password, use_ssl=use_ssl, use_tls=not use_ssl) as s:
        for from_addr, to_addrs, raw in payloads:
            # smtplib expects a list for to_addrs
            if isinstance(to_addrs, str):
                to_list = [to_addrs]
            else:
                to_list = list(to_addrs)
            s.sendmail(from_addr, to_list, raw)
            sent += 1
    return sent


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
    msg = MIMEText(html_body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = user
    if isinstance(to_email, (list, tuple)):
        msg["To"] = ", ".join(to_email)
        to_addrs = list(to_email)
    else:
        msg["To"] = to_email
        to_addrs = [to_email]

    # Reuse one connection under the hood (fast path), no format changes
    _send_bulk_raw_auto(
        host=host,
        port=port,
        username=user,
        password=password,
        payloads=[(user, to_addrs, msg.as_string())],
    )