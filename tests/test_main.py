import unittest
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, date
import pytz
from dotenv import load_dotenv

import main
from app.render import build_html

# Load environment variables for tests
load_dotenv()

class TestMainApplication(unittest.TestCase):
    """Test main application logic"""
    
    def setUp(self):
        self.tz = pytz.timezone("America/New_York")
    
    def test_load_config(self):
        """Test configuration loading"""
        config = main.load_config()
        
        # Check that all required config keys exist
        required_keys = [
            "to_email", "smtp_host", "smtp_port", "smtp_user", "smtp_pass",
            "timezone", "ics_urls", "notion_token", "db_map"
        ]
        
        for key in required_keys:
            self.assertIn(key, config)
        
        # Check that database map loaded from config.yaml
        self.assertIsInstance(config["db_map"], dict)
        
        # Should have our two databases
        if len(config["db_map"]) > 0:
            for db_id, db_config in config["db_map"].items():
                self.assertIn("name", db_config)
                self.assertIn("date_property", db_config)
                self.assertIn("fields", db_config)
    
    def test_build_html_with_data(self):
        """Test HTML generation with sample data"""
        # Sample calendar events
        now = datetime.now(self.tz)
        events = [
            {
                "title": "Team Meeting",
                "start": now.replace(hour=9, minute=0),
                "end": now.replace(hour=10, minute=0),
                "location": "Conference Room A",
                "notes": "Weekly sync",
                "calendar": "Work Calendar"
            },
            {
                "title": "Lunch with Client", 
                "start": now.replace(hour=12, minute=0),
                "end": now.replace(hour=13, minute=30),
                "location": "Restaurant XYZ",
                "notes": "",
                "calendar": "Work Calendar"
            }
        ]
        
        # Sample due items
        due_today = [
            {
                "title": "Submit Project Proposal",
                "url": "https://notion.so/task1",
                "notes": "Include budget breakdown",
                "db_name": "Tasks",
                "fields": {"Priority": "High", "Category": "Work"}
            }
        ]
        
        due_tomorrow = [
            {
                "title": "Review Design Document",
                "url": "https://notion.so/task2", 
                "notes": "Focus on user experience section",
                "db_name": "Projects",
                "fields": {"Status": "In Progress", "Owner": "Team Lead"}
            }
        ]
        
        html = build_html(self.tz, events, due_today, due_tomorrow)
        
        # Check that HTML contains expected content
        self.assertIn("Team Meeting", html)
        self.assertIn("Lunch with Client", html)
        self.assertIn("Submit Project Proposal", html)
        self.assertIn("Review Design Document", html)
        self.assertIn("Conference Room A", html)
        self.assertIn("High", html)  # Priority field
        self.assertIn("Team Lead", html)  # Owner field
        
        # Check for structure
        self.assertIn("Due today", html)
        self.assertIn("Due tomorrow", html)
        
        # Should be valid HTML fragment
        self.assertIn("<div", html.lower())
        self.assertIn("</div>", html.lower())
    
    def test_build_html_empty_data(self):
        """Test HTML generation with no events or tasks"""
        html = build_html(self.tz, [], [], [])
        
        # Should still generate valid HTML
        self.assertIsInstance(html, str)
        self.assertGreater(len(html), 100)  # Should have some basic structure
    
    @patch('main.send_email')
    @patch('main.build_html')
    @patch('main.query_due_on')
    @patch('main.fetch_ics_events_for_day')
    def test_run_once_integration(self, mock_fetch_events, mock_query_due, mock_build_html, mock_send_email):
        """Test the main run_once function with mocked dependencies"""
        # Setup mocks
        mock_fetch_events.return_value = []
        mock_query_due.return_value = []
        mock_build_html.return_value = "<html>Test</html>"
        mock_send_email.return_value = None
        
        # Run the function
        main.run_once()
        
        # Verify all functions were called
        mock_fetch_events.assert_called_once()
        self.assertEqual(mock_query_due.call_count, 2)  # Called for today and tomorrow
        mock_build_html.assert_called_once()
        mock_send_email.assert_called_once()

if __name__ == "__main__":
    unittest.main()
