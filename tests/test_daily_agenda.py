import unittest
from datetime import datetime, timedelta
import pytz

import old.daily_agenda as da

class TestAgendaSimple(unittest.TestCase):
    def setUp(self):
        da.TZ = pytz.timezone("America/New_York")

    def test_minutes_between(self):
        a_end = da.TZ.localize(datetime(2025, 8, 13, 9, 0))
        b_start = da.TZ.localize(datetime(2025, 8, 13, 9, 12))
        self.assertEqual(da.minutes_between(a_end, b_start), 12)

    def test_overlap_badge_in_html(self):
        # Two overlapping events: 9:00–10:00 and 9:30–10:30
        e1_start = da.TZ.localize(datetime(2025, 8, 13, 9, 0))
        e1_end   = da.TZ.localize(datetime(2025, 8, 13, 10, 0))
        e2_start = da.TZ.localize(datetime(2025, 8, 13, 9, 30))
        e2_end   = da.TZ.localize(datetime(2025, 8, 13, 10, 30))
        events = [
            {"title":"A","start":e1_start,"end":e1_end,"location":"","notes":"","calendar":"Cal X"},
            {"title":"B","start":e2_start,"end":e2_end,"location":"","notes":"","calendar":"Cal Y"},
        ]
        html = da.build_html(events, [], [])
        self.assertIn("⚠︎ overlaps", html)
        # Calendar labels should be visible
        self.assertIn("(Cal X)", html)
        self.assertIn("(Cal Y)", html)

    def test_due_lists_render(self):
        # No events, but has due items
        due_today = [{"title":"HW 1","url":"https://notion.so/x","notes":"finish Q3"}]
        due_tomorrow = [{"title":"Lab","url":"https://notion.so/y","notes":""}]
        html = da.build_html([], due_today, due_tomorrow)
        self.assertIn("HW 1", html)
        self.assertIn("Lab", html)
        self.assertIn("Due today", html)
        self.assertIn("Due tomorrow", html)

if __name__ == "__main__":
    unittest.main()