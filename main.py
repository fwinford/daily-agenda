import os, yaml, pytz
from datetime import datetime, timedelta

from app.calendars import fetch_ics_events_for_day
from app.notion import query_due_on
from app.render import build_html
from app.emailer import send_email

def load_config():
    """Read .env from environment and databases from config.yaml."""
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
    # load database map
    db_map = {}
    if os.path.exists("config.yaml"):
        with open("config.yaml","r") as f:
            y = yaml.safe_load(f) or {}
            for db_id, cfg in (y.get("databases") or {}).items():
                db_map[str(db_id)] = {
                    "name": cfg.get("name"),
                    "date_property": cfg.get("date_property") or "Date",
                    "fields": cfg.get("fields") or [],
                }
    settings["db_map"] = db_map
    return settings

def run_once():
    cfg = load_config()
    tz = pytz.timezone(cfg["timezone"])
    now = datetime.now(tz)
    today = now.date()
    tomorrow = (now + timedelta(days=1)).date()

    events = fetch_ics_events_for_day(cfg["ics_urls"], tz, today)
    due_today = query_due_on(cfg["notion_token"], cfg["db_map"], today)
    due_tomorrow = query_due_on(cfg["notion_token"], cfg["db_map"], tomorrow)

    html = build_html(tz, events, due_today, due_tomorrow)
    subject = f"Agenda for {now.strftime('%a, %b %-d')}"

    send_email(cfg["smtp_host"], cfg["smtp_port"], cfg["smtp_user"], cfg["smtp_pass"],
               cfg["to_email"], subject, html)

if __name__ == "__main__":
    run_once()