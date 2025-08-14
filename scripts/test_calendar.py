#!/usr/bin/env python3
"""
Calendar testing script to debug ICS URL access
This helps test different Google Calendar URL formats to find the working one.
"""

import requests
import sys
import os
from datetime import datetime, date
import pytz

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.calendars import fetch_ics_events_for_day

def test_google_calendar_urls(calendar_id):
    """Test different Google Calendar ICS URL formats"""
    
    base_formats = [
        f"https://calendar.google.com/calendar/ical/{calendar_id}/public/basic.ics",
        f"https://calendar.google.com/calendar/ical/{calendar_id}/private/basic.ics", 
        f"https://calendar.google.com/calendar/ical/{calendar_id}/public/basic",
        f"https://calendar.google.com/calendar/ical/{calendar_id}/private/basic",
        f"https://calendar.google.com/calendar/ical/{calendar_id}/basic.ics",
        f"https://calendar.google.com/calendar/ical/{calendar_id}/basic",
    ]
    
    print(f"Testing calendar ID: {calendar_id}")
    print("-" * 60)
    
    for url in base_formats:
        try:
            response = requests.get(url, timeout=10)
            status = response.status_code
            content_type = response.headers.get('content-type', '')
            content_length = len(response.text)
            
            print(f"URL: {url}")
            print(f"Status: {status}")
            print(f"Content-Type: {content_type}")
            print(f"Content Length: {content_length}")
            
            if status == 200 and content_length > 100:
                print("✅ SUCCESS - This URL works!")
                # Test if it has events
                try:
                    tz = pytz.timezone("America/New_York")
                    today = date.today()
                    events = fetch_ics_events_for_day([url], tz, today)
                    print(f"📅 Found {len(events)} events for today")
                    if events:
                        for event in events[:3]:  # Show first 3 events
                            print(f"   - {event['title']} at {event['start']}")
                except Exception as e:
                    print(f"❌ Error parsing events: {e}")
            else:
                print("❌ Failed")
            
            print("-" * 60)
            
        except Exception as e:
            print(f"URL: {url}")
            print(f"❌ Error: {e}")
            print("-" * 60)

def main():
    # Test the NYU calendar
    calendar_id = "nyu.edu_85g8jojlffa2il0dhrb0ciihrg%40group.calendar.google.com"
    test_google_calendar_urls(calendar_id)
    
    print("\n" + "="*60)
    print("CURRENT ICS URLS TEST")
    print("="*60)
    
    # Test current working URLs
    from dotenv import load_dotenv
    load_dotenv()
    
    ics_urls = [u.strip() for u in os.getenv("ICS_URLS","").split(",") if u.strip()]
    tz = pytz.timezone("America/New_York") 
    today = date.today()
    
    print(f"Testing {len(ics_urls)} calendar URLs for {today}")
    
    for i, url in enumerate(ics_urls, 1):
        print(f"\nCalendar {i}: {url[:50]}...")
        try:
            events = fetch_ics_events_for_day([url], tz, today)
            print(f"✅ Found {len(events)} events")
            if events:
                for event in events[:2]:
                    print(f"   - {event['title']}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
