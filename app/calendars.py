"""
Calendar Integration Module

This module handles fetching and parsing calendar events from ICS feeds.
It supports multiple calendar sources (iCloud, Google Calendar, etc.) and
converts them into a unified format for the daily agenda.

Key features:
- Fetches ICS feeds from multiple URLs
- Handles timezone conversions properly
- Detects all-day events automatically
- Filters events to only include those on the target date
- Graceful error handling for network/parsing failures
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict
import pytz, requests
from icalendar import Calendar

def _to_local(dt_obj, tz):
    """
    Convert iCalendar date/datetime objects to timezone-aware local datetime.
    
    iCalendar dates can come in various formats:
    - Naive datetime (assumed UTC)
    - Timezone-aware datetime
    - Date-only objects (converted to midnight in local timezone)
    
    Args:
        dt_obj: Date or datetime object from iCalendar
        tz: Target timezone to convert to
        
    Returns:
        datetime: Timezone-aware datetime in the target timezone
    """
    if isinstance(dt_obj, datetime):
        # Handle datetime objects
        if dt_obj.tzinfo is None:
            # Naive datetime assumed to be UTC
            dt_obj = pytz.utc.localize(dt_obj)
        return dt_obj.astimezone(tz)
    
    # Handle date-only objects (convert to midnight in local timezone)
    return tz.localize(datetime(dt_obj.year, dt_obj.month, dt_obj.day))

def _short_name_from_url(url: str) -> str:
    """
    Extract a calendar name from the ICS URL as fallback.
    
    When the calendar doesn't have an X-WR-CALNAME property,
    we try to make a reasonable name from the URL.
    
    Args:
        url (str): The ICS feed URL
        
    Returns:
        str: Short calendar name for display
    """
    # Extract filename from URL and remove .ics extension
    name = url.split("/")[-1].split("?")[0]
    return re.sub(r"\.ics$", "", name, flags=re.I) or "Calendar"

def fetch_ics_events_for_day(ics_urls: List[str], tz, target_date) -> List[Dict]:
    """
    Fetch and parse calendar events from multiple ICS feeds for a specific date.
    
    This is the main function that:
    1. Downloads ICS feeds from all provided URLs
    2. Parses the calendar data
    3. Extracts events that overlap with the target date
    4. Converts them to a standard format for display
    
    Args:
        ics_urls (List[str]): List of ICS feed URLs to fetch
        tz: Timezone object for date calculations
        target_date: Date object for which to fetch events
        
    Returns:
        List[Dict]: List of events, each containing:
                   - title: Event title
                   - start: Start datetime (timezone-aware)
                   - end: End datetime (timezone-aware)
                   - location: Event location (string)
                   - notes: Event description/notes
                   - calendar: Calendar name
                   - all_day: Boolean indicating if it's an all-day event
    """
    events = []
    
    # Calculate the day boundaries in local timezone
    day_start = tz.localize(datetime(target_date.year, target_date.month, target_date.day))
    day_end = day_start + timedelta(days=1)

    # Process each calendar feed
    for url in ics_urls:
        try:
            # Download the ICS feed
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            
            # Parse the calendar data
            cal = Calendar.from_ical(r.content)
            calname = str(cal.get("X-WR-CALNAME", "")) or _short_name_from_url(url)

            # Process each event in the calendar
            for comp in cal.walk("VEVENT"):
                # Extract basic date/time information
                dtstart = comp.get("dtstart").dt
                dtend = comp.get("dtend").dt
                start = _to_local(dtstart, tz)
                end   = _to_local(dtend, tz)

                # Determine if this is an all-day event
                # Method 1: Check if the original was a date object (not datetime)
                is_all_day = not isinstance(dtstart, datetime)
                
                # Method 2: Check for events that start at midnight and last most of the day
                if not is_all_day:
                    dur = end - start
                    if start.hour == 0 and start.minute == 0 and dur >= timedelta(hours=23, minutes=30):
                        is_all_day = True

                # Filter: only include events that overlap with our target day
                if end <= day_start or start >= day_end:
                    continue

                # Build the event object for display
                events.append({
                    "title": str(comp.get("summary", "(No title)")),
                    "start": start,
                    "end": end,
                    "location": str(comp.get("location", "") or ""),
                    "notes": str(comp.get("description", "") or ""),
                    "calendar": calname,
                    "all_day": is_all_day,
                })
                
        except Exception:
            # Silently skip calendars that fail to load
            # This prevents one broken calendar from breaking the entire agenda
            continue

    # Sort events by start time for consistent display
    events.sort(key=lambda e: e["start"])
    return events