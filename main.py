"""
Daily Agenda - Main Entry Point

This script orchestrates the daily agenda generation process:
1. Loads configuration from .env and config.yaml
2. Fetches calendar events for today
3. Queries Notion databases for tasks due today and tomorrow
4. Generates HTML email content
5. Sends the agenda via email

Usage: python main.py
"""

import os, yaml, pytz
from datetime import datetime, timedelta
from dotenv import load_dotenv

from app.calendars import fetch_ics_events_for_day
from app.notion import query_due_on
from app.render import build_html
from app.emailer import send_email


# Load environment variables from config/.env file
load_dotenv("config/.env")

def load_config():
    """
    Load and validate configuration from environment variables and config.yaml
    
    Returns:
        dict: Configuration dictionary with all required settings including:
              - Email settings (SMTP host, port, credentials)
              - Timezone configuration
              - Notion API token
              - Calendar ICS URLs
              - Database mapping from config.yaml
    """
    # Load basic email and API settings from environment variables
    settings = {
        "to_email": os.getenv("TO_EMAIL"),
        "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "smtp_user": os.getenv("SMTP_USER"),
        "smtp_pass": os.getenv("SMTP_PASS"),
        "timezone": os.getenv("TIMEZONE", "America/New_York"),
        "ics_urls": [u.strip() for u in os.getenv("ICS_URLS","").split(",") if u.strip()],
        "notion_token": os.getenv("NOTION_TOKEN",""),
    }
    
    # Load database configuration from config/config.yaml
    # This maps database IDs to their configuration (date fields, extra fields to show)
    db_map = {}
    config_path = "config/config.yaml"
    if os.path.exists(config_path):
        with open(config_path,"r") as f:
            y = yaml.safe_load(f) or {}
            for db_id, cfg in (y.get("databases") or {}).items():
                db_map[str(db_id)] = {
                    "name": cfg.get("name"),
                    "date_property": cfg.get("date_property") or "Date",
                    "fields": cfg.get("fields") or [],
                }
    settings["db_map"] = db_map
    return settings

def run_once(target_date=None, preview_only=False):
    """
    Main function that orchestrates the daily agenda generation process:
    
    1. Sets up timezone and calculates today/tomorrow dates
    2. Fetches calendar events from ICS URLs
    3. Queries Notion databases for tasks due today and tomorrow
    4. Builds HTML email content from the collected data
    5. Sends the final agenda email
    
    Args:
        target_date (datetime.date, optional): Specific date to generate agenda for.
                                             If None, uses current date.
        preview_only (bool): If True, returns HTML without sending email
    
    Returns:
        str: HTML content (only if preview_only=True)
    """
    # Load configuration and set up timezone calculations
    cfg = load_config()
    tz = pytz.timezone(cfg["timezone"])
    
    if target_date:
        # Use provided date and create a datetime object for that day
        today = target_date
        # Create a datetime at noon for that day to get proper formatting
        now = tz.localize(datetime.combine(today, datetime.min.time().replace(hour=12)))
        tomorrow = today + timedelta(days=1)
    else:
        # Use current date/time
        now = datetime.now(tz)
        today = now.date()
        tomorrow = (now + timedelta(days=1)).date()

    # Fetch data from external sources
    events = fetch_ics_events_for_day(cfg["ics_urls"], tz, today)
    due_today = query_due_on(cfg["notion_token"], cfg["db_map"], today)
    due_tomorrow = query_due_on(cfg["notion_token"], cfg["db_map"], tomorrow)

    # Generate HTML email content from collected data
    html = build_html(tz, events, due_today, due_tomorrow, now)
    
    if preview_only:
        return html
    
    # Send the final email
    subject = f"Agenda for {now.strftime('%a, %b %-d')}"
    send_email(cfg["smtp_host"], cfg["smtp_port"], cfg["smtp_user"], cfg["smtp_pass"],
               cfg["to_email"], subject, html)
    print("Email sent successfully!")

if __name__ == "__main__":
    run_once()