"""
Daily Agenda Emailer
--------------------
Pulls today's events from one or more ICS calendars (e.g., iCloud/Google),
optionally pulls "due" items from one or more Notion databases, and emails
a single, nicely formatted HTML digest.

New in this version:
- Shows calendar name for each event
- Flags tight gaps (< 15 minutes) and overlapping events (⚠︎ overlaps)
- Notion: per-database date property + extra fields (e.g., Type, Company, Class)
- Shows the *database name* next to each due item
"""

import os
import re
import html
import math
import smtplib
from datetime import datetime, timedelta

import pytz
import requests
from icalendar import Calendar
from email.mime.text import MIMEText

# -------- config from env (edit your .env) --------
TO_EMAIL = os.getenv("TO_EMAIL")                                  # destination email
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")              # SMTP server hostname
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))                    # SMTP server port
SMTP_USER = os.getenv("SMTP_USER")                                # SMTP login (email)
SMTP_PASS = os.getenv("SMTP_PASS")                                # SMTP app password
TIMEZONE = os.getenv("TIMEZONE", "America/New_York")              # IANA tz name
ICS_URLS = [u.strip() for u in os.getenv("ICS_URLS", "").split(",") if u.strip()]  # .ics URLs (comma-sep)
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")                      # Notion integration token (secret_...)
NOTION_DB_IDS = [d.strip() for d in os.getenv("NOTION_DB_IDS", "").split(",") if d.strip()]
NOTION_DUE_PROP = os.getenv("NOTION_DUE_PROP", "Date")            # default date property name
GMAPS_KEY = os.getenv("GMAPS_KEY")                                # optional Google Maps API key
ORIGIN_ADDRESS = os.getenv("ORIGIN_ADDRESS", "")                  # optional origin for travel time

# ---- per-database overrides for your workspace (easy to edit) ----
# Map a DB ID -> the *date* property to use for filtering "due on this day".
DB_DATE_PROP = {
    # Your first DB (applications): uses "Deadline"
    "32ee4d67321745fa8af54885b1bc28d6": "Deadline",
    # Your second DB (homework/classes): uses "Date"
    "f3877a9dfce74e0792454cc6a20be80e": "Date",
}
# Map a DB ID -> list of extra fields to display under each item.
DB_EXTRA_FIELDS = {
    # show Type + Company for the first DB
    "32ee4d67321745fa8af54885b1bc28d6": ["Type", "Company"],
    # show Class + Type for the second DB
    "f3877a9dfce74e0792454cc6a20be80e": ["Class", "Type"],
}

# Cache for database titles so we only look them up once per run
_DB_TITLE_CACHE = {}

# Global timezone object
TZ = pytz.timezone(TIMEZONE)


# -- Time normalization helper: convert iCal date/datetime into your local timezone
def _to_local(dt_obj):
    """
    Convert an iCal dt (date OR datetime, tz-naive OR tz-aware) into a TZ-aware
    datetime in the user's local timezone (TZ).
    - All-day dates become local midnight.
    - Naive datetimes are assumed UTC, then converted (safe default).
    """
    if isinstance(dt_obj, datetime):
        if dt_obj.tzinfo is None:
            dt_obj = pytz.utc.localize(dt_obj)
        return dt_obj.astimezone(TZ)
    else:
        # dt_obj is a date (no time)
        return TZ.localize(datetime(dt_obj.year, dt_obj.month, dt_obj.day))


# -- Utility: readable name if X-WR-CALNAME is missing from the feed
def _short_name_from_url(url: str) -> str:
    """
    Derive a human-ish calendar name from an ICS URL if the feed doesn't include
    X-WR-CALNAME. Best effort only.
    """
    name = url.split("/")[-1].split("?")[0]
    name = re.sub(r"\.ics$", "", name, flags=re.I)
    return name or "Calendar"


# -- Utility: extract a human string from a Notion property object
def _prop_to_text(prop):
    """
    Turn a Notion property payload into readable text.
    Supports: title, rich_text, select, multi_select, people, url, email, phone_number.
    Falls back to empty string if not recognized.
    """
    if not isinstance(prop, dict) or "type" not in prop:
        return ""
    t = prop["type"]
    if t == "title":
        return "".join(span.get("plain_text", "") for span in prop.get("title", []))
    if t == "rich_text":
        return "".join(span.get("plain_text", "") for span in prop.get("rich_text", []))
    if t == "select":
        return (prop.get("select") or {}).get("name", "") or ""
    if t == "multi_select":
        return ", ".join(tag.get("name", "") for tag in prop.get("multi_select", []))
    if t == "people":
        return ", ".join(p.get("name") or p.get("id", "") for p in prop.get("people", []))
    if t == "url":
        return prop.get("url") or ""
    if t == "email":
        return prop.get("email") or ""
    if t == "phone_number":
        return prop.get("phone_number") or ""
    # date, number, checkbox, etc. can be added as needed
    return ""


# -- Notion: fetch the database title (for display next to items)
def _notion_get_db_title(db_id):
    """
    Retrieve and cache the human name (title) of a Notion database by ID.
    Requires NOTION_TOKEN and a connected integration.
    """
    if db_id in _DB_TITLE_CACHE:
        return _DB_TITLE_CACHE[db_id]
    if not NOTION_TOKEN:
        return "Notion DB"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
    }
    try:
        r = requests.get(f"https://api.notion.com/v1/databases/{db_id}", headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()
        title = "".join(t.get("plain_text", "") for t in data.get("title", [])) or "Notion DB"
        _DB_TITLE_CACHE[db_id] = title
        return title
    except Exception:
        return "Notion DB"


# -- Pull and merge all ICS events that overlap 'target_date' in local time
def fetch_ics_events_for_day(target_date):
    """
    Download each ICS feed in ICS_URLS and return a sorted list of events that
    overlap the target_date (local time).

    Each event dict contains:
    {
      "title": str,
      "start": datetime (TZ-aware),
      "end": datetime (TZ-aware),
      "location": str,
      "notes": str,
      "calendar": str   # calendar label
    }
    """
    events = []
    day_start = TZ.localize(datetime(target_date.year, target_date.month, target_date.day))
    day_end = day_start + timedelta(days=1)

    for url in ICS_URLS:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        cal = Calendar.from_ical(r.content)

        # Prefer feed-provided name; otherwise derive from URL
        calname = str(cal.get("X-WR-CALNAME", "")) or _short_name_from_url(url)

        for comp in cal.walk("VEVENT"):
            dtstart = comp.get("dtstart").dt
            dtend = comp.get("dtend").dt
            start = _to_local(dtstart)
            end = _to_local(dtend)

            # Keep events that overlap [day_start, day_end)
            if end <= day_start or start >= day_end:
                continue

            title = str(comp.get("summary", "(No title)"))
            location = str(comp.get("location", "") or "")
            desc = str(comp.get("description", "") or "")

            events.append({
                "title": title,
                "start": start,
                "end": end,
                "location": location,
                "notes": desc,
                "calendar": calname,
            })

    events.sort(key=lambda e: e["start"])
    return events


# -- Query Notion for items due on a given date across one or more databases
def notion_query_due_on(date_obj):
    """
    Return pages whose date property equals the given local date.
    Uses per-DB date property from DB_DATE_PROP if present, else NOTION_DUE_PROP.

    Returns a list of dicts:
      {
        "title": str,
        "url": str,
        "notes": str,
        "db_name": str,
        "fields": { "Type": "...", "Company": "...", ... }   # per DB_EXTRA_FIELDS
      }
    """
    if not NOTION_TOKEN or not NOTION_DB_IDS:
        return []

    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

    iso_day = date_obj.strftime("%Y-%m-%d")
    results = []

    for db in NOTION_DB_IDS:
        date_prop = DB_DATE_PROP.get(db, NOTION_DUE_PROP)
        payload = {
            "filter": {
                "property": date_prop,
                "date": {"equals": iso_day}
            },
            "sorts": [{"property": date_prop, "direction": "ascending"}],
            "page_size": 100,
        }

        start_cursor = None
        db_name = _notion_get_db_title(db)
        wanted_fields = DB_EXTRA_FIELDS.get(db, [])

        while True:
            if start_cursor:
                payload["start_cursor"] = start_cursor

            resp = requests.post(
                f"https://api.notion.com/v1/databases/{db}/query",
                headers=headers, json=payload, timeout=30
            )
            resp.raise_for_status()
            data = resp.json()

            for page in data.get("results", []):
                props = page.get("properties", {})

                # title
                title = "(Untitled)"
                for p in props.values():
                    if p.get("type") == "title":
                        if p["title"]:
                            title = "".join(t.get("plain_text","") for t in p["title"]) or "(Untitled)"
                        break

                # optional notes
                notes = ""
                if "Notes" in props and props["Notes"]["type"] == "rich_text":
                    notes = "".join(t.get("plain_text","") for t in props["Notes"]["rich_text"])[:300]

                # extra fields per DB (e.g., Type, Company, Class, etc.)
                fields = {}
                for field_name in wanted_fields:
                    if field_name in props:
                        fields[field_name] = _prop_to_text(props[field_name])

                results.append({
                    "title": title,
                    "url": page.get("url"),
                    "notes": notes,
                    "db_name": db_name,
                    "fields": fields,
                })

            if not data.get("has_more"):
                break
            start_cursor = data.get("next_cursor")

    return results


# -- Simple time gap helper (minutes from end of A to start of B)
def minutes_between(a_end, b_start):
    """
    Compute integer minutes from datetime a_end to datetime b_start.
    Positive means b_start is after a_end; negative means it starts before.
    """
    return int((b_start - a_end).total_seconds() // 60)


# -- Optional: Google Distance Matrix lookup (minutes) for "Leave by" hints
def gm_distance_minutes(origin, dest):
    """
    If GMAPS_KEY and origin/dest are provided, query Distance Matrix and
    return travel minutes (rounded up). Otherwise return None.
    """
    if not GMAPS_KEY or not origin or not dest:
        return None
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {"origins": origin, "destinations": dest, "key": GMAPS_KEY}
    try:
        j = requests.get(url, params=params, timeout=10).json()
        elem = j["rows"][0]["elements"][0]
        if elem.get("status") == "OK":
            return int(math.ceil(elem["duration"]["value"] / 60))
    except Exception:
        return None
    return None


# -- Render the HTML email body (agenda + due today + due tomorrow)
def build_html(today_events, due_today, due_tomorrow):
    """
    Render the HTML digest with:
      - Today's events (show calendar name, flag tight gaps <15 min, flag overlaps)
      - 'Due today' Notion items (with DB name + extra fields)
      - 'Due tomorrow' Notion items (with DB name + extra fields)
    """
    def fmt(dt):
        # %-I works on macOS/Linux; on Windows, use %#I instead
        return dt.strftime("%-I:%M %p")

    # Compute overlap flags: O(n^2) - sufficient for daily event counts
    n = len(today_events)
    overlapped = [False] * n
    for i in range(n):
        for j in range(i):
            if (today_events[i]["start"] < today_events[j]["end"]
                and today_events[j]["start"] < today_events[i]["end"]):
                overlapped[i] = True
                overlapped[j] = True

    day_label = (today_events[0]["start"].strftime("%A, %B %-d")
                 if today_events else datetime.now(TZ).strftime("%A, %B %-d"))

    rows = []
    prev_end = None
    prev_loc = ORIGIN_ADDRESS or ""

    for idx, e in enumerate(today_events):
        # tight turnaround flag
        gap = ""
        if prev_end:
            gap_min = minutes_between(prev_end, e["start"])
            if 0 <= gap_min < 15:
                gap = f' <span style="color:#c00;">• only {gap_min} min gap</span>'

        # overlap flag
        overlap_badge = ' <span style="color:#c00;">⚠︎ overlaps</span>' if overlapped[idx] else ""

        # travel time / leave by
        leave_by = ""
        if e["location"]:
            mins = gm_distance_minutes(prev_loc, e["location"])
            if mins is not None:
                leave = e["start"] - timedelta(minutes=mins)
                leave_by = f' | <strong>Leave by {fmt(leave)}</strong> (~{mins} min travel)'

        cal_label = html.escape(e.get("calendar", "Calendar"))

        row = f"""
        <tr>
          <td style="white-space:nowrap;padding:6px 10px;vertical-align:top;">{fmt(e["start"])}–{fmt(e["end"])}</td>
          <td style="padding:6px 0;">
            <strong>{html.escape(e["title"])}</strong>
            <span style="color:#666;">({cal_label})</span>{overlap_badge}
            {' | ' + html.escape(e['location']) if e['location'] else ''}{leave_by}{gap}
            {f'<div style="color:#555;font-size:12px;margin-top:2px;">{html.escape(e["notes"][:200])}</div>' if e['notes'] else ''}
          </td>
        </tr>
        """
        rows.append(row)
        prev_end = e["end"]
        prev_loc = e["location"] or prev_loc

    def list_due(items):
        if not items:
            return "<p>Nothing due 🎉</p>"

        def render_fields(d):
            # Convert {"Type":"Internship","Company":"XYZ"} -> "Type: Internship | Company: XYZ"
            pairs = [f"{html.escape(k)}: {html.escape(v)}" for k, v in d.items() if v]
            return " | ".join(pairs)

        lis = []
        for x in items:
            meta = []
            if x.get("db_name"):
                meta.append(f"<span style='color:#666;'>[{html.escape(x['db_name'])}]</span>")
            if x.get("fields"):
                fields_str = render_fields(x["fields"])
                if fields_str:
                    meta.append(fields_str)
            meta_str = " - " + " | ".join(meta) if meta else ""
            notes_str = f" - <span style='color:#555;'>{html.escape(x['notes'])}</span>" if x.get("notes") else ""
            lis.append(
                f'<li><a href="{html.escape(x["url"])}">{html.escape(x["title"])}</a>{meta_str}{notes_str}</li>'
            )
        return "<ul>" + "".join(lis) + "</ul>"

    html_body = f"""
    <div style="font:14px/1.5 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial; max-width:760px;">
      <h2 style="margin:0 0 12px;">Today’s agenda - {day_label}</h2>
      {"<table cellpadding='0' cellspacing='0' style='width:100%;border-collapse:collapse;'>" + "".join(rows) + "</table>" if rows else "<p>No events today.</p>"}
      <h3 style="margin-top:18px;">Due today</h3>
      {list_due(due_today)}
      <h3 style="margin-top:18px;">Due tomorrow</h3>
      {list_due(due_tomorrow)}
      <p style="color:#777;margin-top:16px;">Tips: tight-gap flag = &lt;15 min; '⚠︎ overlaps' shows when events overlap; “Leave by” requires a location + Maps key.</p>
    </div>
    """
    return html_body


# -- SMTP send wrapper: subject + HTML -> delivers via SMTP_HOST/PORT with login
def send_email(subject, html_body):
    """
    Send the HTML digest via SMTP using STARTTLS + login.
    From: SMTP_USER
    To:   TO_EMAIL
    """
    msg = MIMEText(html_body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = TO_EMAIL
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(SMTP_USER, [TO_EMAIL], msg.as_string())


# -- Orchestrator: gather today's events, due items, render, and send
def run():
    """
    Main entrypoint:
      - Compute today/tomorrow in local TZ
      - Fetch ICS events for today
      - Query Notion for due items today/tomorrow
      - Build HTML and send the email
    """
    now = datetime.now(TZ)
    today = now.date()
    tomorrow = (now + timedelta(days=1)).date()

    today_events = fetch_ics_events_for_day(today)
    due_today = notion_query_due_on(today)
    due_tomorrow = notion_query_due_on(tomorrow)

    subject = f"Agenda for {now.strftime('%a, %b %-d')}"
    html_body = build_html(today_events, due_today, due_tomorrow)
    send_email(subject, html_body)


if __name__ == "__main__":
    run()