import unittest
from datetime import datetime, timedelta
import pytz

from app.render import build_html

class TestAgendaSimple(unittest.TestCase):
    def setUp(self):
        self.tz = pytz.timezone("America/New_York")

    def test_overlap_detection_in_html(self):
        """Test that overlapping events are detected and marked in HTML"""
        # Two overlapping events: 9:00–10:00 and 9:30–10:30
        e1_start = self.tz.localize(datetime(2025, 8, 13, 9, 0))
        e1_end   = self.tz.localize(datetime(2025, 8, 13, 10, 0))
        e2_start = self.tz.localize(datetime(2025, 8, 13, 9, 30))
        e2_end   = self.tz.localize(datetime(2025, 8, 13, 10, 30))
        
        events = [
            {
                "title": "Meeting A",
                "start": e1_start,
                "end": e1_end,
                "location": "Room 1",
                "notes": "",
                "calendar": "Cal X"
            },
            {
                "title": "Meeting B", 
                "start": e2_start,
                "end": e2_end,
                "location": "Room 2",
                "notes": "",
                "calendar": "Cal Y"
            },
        ]
        
        html = build_html(self.tz, events, [], [])
        
        # Should detect overlap and show warning
        self.assertIn("overlap", html.lower())
        
        # Calendar labels should be visible
        self.assertIn("Cal X", html)
        self.assertIn("Cal Y", html)

    def test_due_lists_render(self):
        """Test that due items are properly rendered in HTML"""
        # No events, but has due items
        due_today = [
            {
                "title": "Complete Project Report",
                "url": "https://notion.so/x",
                "notes": "Include charts and analysis",
                "db_name": "Tasks",
                "fields": {"Priority": "High", "Category": "Work"}
            }
        ]
        due_tomorrow = [
            {
                "title": "Team Presentation",
                "url": "https://notion.so/y", 
                "notes": "Practice beforehand",
                "db_name": "Projects",
                "fields": {"Status": "Ready", "Owner": "Manager"}
            }
        ]
        
        html = build_html(self.tz, [], due_today, due_tomorrow)
        
        # Check content is present
        self.assertIn("Complete Project Report", html)
        self.assertIn("Team Presentation", html)
        self.assertIn("Due today", html)
        self.assertIn("Due tomorrow", html)
        self.assertIn("High", html)  # Priority field should be shown
        self.assertIn("Manager", html)  # Owner field should be shown
        
    def test_empty_agenda(self):
        """Test rendering with no events or due items"""
        html = build_html(self.tz, [], [], [])
        
        # Should still be valid HTML
        self.assertIsInstance(html, str)
        self.assertGreater(len(html), 50)  # Should have basic structure

if __name__ == "__main__":
    unittest.main()