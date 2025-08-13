import re
from datetime import datetime, timedelta
from typing import List, Dict
import pytz, requests
from icalendar import Calendar

def _to_local(dt_obj, tz):
    """Normalize iCal date/datetime into tz-aware local datetime."""
    if isinstance(dt_obj, datetime):
        if dt_obj.tzinfo is None:
            dt_obj = pytz.utc.localize(dt_obj)
        return dt_obj.astimezone(tz)
    return tz.localize(datetime(dt_obj.year, dt_obj.month, dt_obj.day))

def _short_name_from_url(url: str) -> str:
    """Fallback calendar name when X-WR-CALNAME missing."""
    name = url.split("/")[-1].split("?")[0]
    return re.sub(r"\.ics$", "", name, flags=re.I) or "Calendar"

def fetch_ics_events_for_day(ics_urls: List[str], tz, target_date) -> List[Dict]:
    """
    Read all ICS feeds and return events overlapping target_date.
    Each event: {title,start,end,location,notes,calendar,all_day}
    """
    events = []
    day_start = tz.localize(datetime(target_date.year, target_date.month, target_date.day))
    day_end = day_start + timedelta(days=1)

    for url in ics_urls:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        cal = Calendar.from_ical(r.content)
        calname = str(cal.get("X-WR-CALNAME", "")) or _short_name_from_url(url)

        for comp in cal.walk("VEVENT"):
            dtstart = comp.get("dtstart").dt
            dtend = comp.get("dtend").dt
            start = _to_local(dtstart, tz)
            end   = _to_local(dtend, tz)

            # determine all-day
            is_all_day = not isinstance(dtstart, datetime)
            if not is_all_day:
                dur = end - start
                if start.hour == 0 and start.minute == 0 and dur >= timedelta(hours=23, minutes=30):
                    is_all_day = True

            # overlap check with the day window
            if end <= day_start or start >= day_end:
                continue

            events.append({
                "title": str(comp.get("summary", "(No title)")),
                "start": start,
                "end": end,
                "location": str(comp.get("location", "") or ""),
                "notes": str(comp.get("description", "") or ""),
                "calendar": calname,
                "all_day": is_all_day,
            })

    events.sort(key=lambda e: e["start"])
    return events