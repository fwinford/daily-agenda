import unittest
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, date
import pytz
from dotenv import load_dotenv

from app.calendars import fetch_ics_events_for_day

# Load environment variables for tests
load_dotenv()

class TestCalendars(unittest.TestCase):
    """Test calendar functionality"""
    
    def setUp(self):
        self.tz = pytz.timezone("America/New_York")
        self.test_date = date(2025, 8, 13)
        self.ics_urls = [u.strip() for u in os.getenv("ICS_URLS", "").split(",") if u.strip()]
    
    def test_fetch_ics_events_empty_urls(self):
        """Test fetching events with empty URL list"""
        events = fetch_ics_events_for_day([], self.tz, self.test_date)
        self.assertEqual(events, [])
    
    @patch('app.calendars.requests.get')
    def test_fetch_ics_events_mock(self, mock_get):
        """Test fetching events with mocked ICS response"""
        # Mock ICS calendar data
        mock_ics_data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:Test
BEGIN:VEVENT
UID:test-event-1
DTSTART:20250813T140000Z
DTEND:20250813T150000Z
SUMMARY:Test Meeting
DESCRIPTION:A test meeting
LOCATION:Conference Room
END:VEVENT
END:VCALENDAR"""
        
        mock_response = MagicMock()
        mock_response.text = mock_ics_data
        mock_response.content = mock_ics_data.encode('utf-8')  # Added content as bytes
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        events = fetch_ics_events_for_day(["http://test.com/cal.ics"], self.tz, self.test_date)
        
        # Should have found the test event
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["title"], "Test Meeting")
        self.assertEqual(events[0]["location"], "Conference Room")
        self.assertEqual(events[0]["notes"], "A test meeting")
    
    @unittest.skipIf(not os.getenv("ICS_URLS"), "ICS_URLS not set")
    def test_fetch_real_calendar_events(self):
        """Integration test - fetch real calendar events"""
        if not self.ics_urls:
            self.skipTest("No ICS URLs configured")
            
        events = fetch_ics_events_for_day(self.ics_urls, self.tz, self.test_date)
        
        # Should return a list
        self.assertIsInstance(events, list)
        
        # Each event should have required fields
        for event in events:
            self.assertIn("title", event)
            self.assertIn("start", event)
            self.assertIn("end", event)
            self.assertIn("location", event)
            self.assertIn("notes", event)
            self.assertIn("calendar", event)
            
            # Times should be datetime objects
            self.assertIsInstance(event["start"], datetime)
            self.assertIsInstance(event["end"], datetime)
    
    @patch('app.calendars.requests.get')
    def test_fetch_ics_events_error_handling(self, mock_get):
        """Test error handling when ICS fetch fails"""
        mock_get.side_effect = Exception("Network error")
        
        # Should not raise exception, just return empty list
        try:
            events = fetch_ics_events_for_day(["http://bad-url.com/cal.ics"], self.tz, self.test_date)
            self.assertEqual(events, [])
        except Exception:
            # If the function doesn't handle errors gracefully, that's also something to note
            self.fail("fetch_ics_events_for_day should handle network errors gracefully")

if __name__ == "__main__":
    unittest.main()
