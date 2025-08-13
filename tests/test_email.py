import unittest
import os
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv
import smtplib

from app.emailer import send_email

# Load environment variables for tests
load_dotenv()

class TestEmailer(unittest.TestCase):
    """Test email functionality"""
    
    def setUp(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "465"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_pass = os.getenv("SMTP_PASS")
        self.to_email = os.getenv("TO_EMAIL")
        
        self.test_subject = "Test Email"
        self.test_html = "<h1>Test</h1><p>This is a test email.</p>"
    
    @patch('app.emailer.smtplib.SMTP_SSL')
    def test_send_email_ssl(self, mock_smtp_ssl):
        """Test sending email with SSL (port 465)"""
        mock_server = MagicMock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server
        
        send_email(
            self.smtp_host, 465, self.smtp_user, self.smtp_pass,
            self.to_email, self.test_subject, self.test_html
        )
        
        # Verify SSL connection was used
        mock_smtp_ssl.assert_called_once()
        mock_server.login.assert_called_once_with(self.smtp_user, self.smtp_pass)
        mock_server.sendmail.assert_called_once()
    
    @patch('app.emailer.smtplib.SMTP')
    def test_send_email_tls(self, mock_smtp):
        """Test sending email with TLS (port 587)"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        send_email(
            self.smtp_host, 587, self.smtp_user, self.smtp_pass,
            self.to_email, self.test_subject, self.test_html
        )
        
        # Verify TLS connection was used
        mock_smtp.assert_called_once()
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with(self.smtp_user, self.smtp_pass)
        mock_server.sendmail.assert_called_once()
    
    @unittest.skipIf(not all([os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"), os.getenv("TO_EMAIL")]), 
                     "Email credentials not set")
    def test_send_real_email(self):
        """Integration test - sends a real test email"""
        if not all([self.smtp_user, self.smtp_pass, self.to_email]):
            self.skipTest("Email credentials not available")
            
        try:
            send_email(
                self.smtp_host, self.smtp_port, self.smtp_user, self.smtp_pass,
                self.to_email, "Daily Agenda Unit Test", 
                "<h2>✓ Unit Test Email</h2><p>If you see this, the email system is working!</p>"
            )
        except Exception as e:
            self.fail(f"Failed to send real email: {e}")

if __name__ == "__main__":
    unittest.main()
