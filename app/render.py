"""
HTML Rendering Module for Daily Agenda

This module handles generating the HTML content for daily agenda emails.
It takes calendar events and Notion tasks and creates a formatted HTML
layout that's easy to read in email clients.

Key features:
- Separates all-day events from timed events
- Detects overlapping calendar events
- Formats Notion task fields nicely
- Creates responsive HTML that works in email clients
"""

from typing import List, Dict
from datetime import datetime
import html


def minutes_between(a_end, b_start):
    """
    Calculate minutes between two datetime objects.
    
    Used for detecting "tight gaps" between calendar events.
    
    Args:
        a_end (datetime): End time of first event
        b_start (datetime): Start time of second event
        
    Returns:
        int: Number of minutes between events (can be negative for overlaps)
    """
    return int((b_start - a_end).total_seconds() // 60)


def _fmt_time(dt: datetime) -> str:
    """
    Format datetime as readable time string.
    
    Handles cross-platform time formatting (macOS/Linux vs Windows).
    
    Args:
        dt (datetime): Datetime object to format
        
    Returns:
        str: Formatted time like "2:30 PM"
    """
    try:
        return dt.strftime("%-I:%M %p")  # macOS/Linux format
    except ValueError:
        return dt.strftime("%#I:%M %p")  # Windows format


def _render_due_list(items: List[Dict]) -> str:
    """
    Render a list of Notion tasks as HTML.
    
    Creates a calm, unbulleted list with task titles, database pills,
    and metadata. Each task is linked to its Notion page.
    
    Args:
        items (List[Dict]): List of task dictionaries from Notion
        
    Returns:
        str: HTML string containing the task list
    """
    if not items:
        return "<p style='color:#666; margin:8px 0;'>Nothing due</p>"

    def render_fields(task_dict):
        """Helper function to format the extra fields for a task"""
        field_parts = []
        
        # Add custom fields (Priority, Type, etc.)
        if "fields" in task_dict:
            for field_name, field_value in task_dict["fields"].items():
                if field_value:  # Only show fields that have values
                    field_parts.append(f"{field_name}: {field_value}")
        
        return " · ".join(field_parts)

    def truncate_notes(notes, max_words=8):
        """Truncate notes to first few words"""
        if not notes:
            return ""
        words = notes.split()
        if len(words) <= max_words:
            return notes
        return " ".join(words[:max_words]) + "..."

    # Build the clean list
    list_items = []
    for item in items:
        title = html.escape(item.get("title", "Untitled"))
        url = item.get("url", "#")
        notes = truncate_notes(item.get("notes", ""))
        db_name = item.get("db_name", "")
        
        # First line: pill + linked title
        pill_html = ""
        if db_name:
            pill_html = f'<span style="background:#f3f4f6; color:#6b7280; padding:2px 8px; border-radius:12px; font-size:12px; margin-right:8px;">{db_name.lower()}</span>'
        
        title_html = f'<span style="color:#94a3b8; margin-right:6px;">✮</span>{pill_html}<a href="{url}" style="color:#3b82f6; text-decoration:none;">{title}</a>'
        
        # Second line: metadata and notes
        metadata_parts = []
        fields_html = render_fields(item)
        if fields_html:
            metadata_parts.append(fields_html)
        if notes:
            metadata_parts.append(f'<span style="color:#9ca3af;">{html.escape(notes)}</span>')
        
        metadata_html = ""
        if metadata_parts:
            metadata_html = f'<div style="font-size:13px; color:#6b7280; margin-top:2px;">{" · ".join(metadata_parts)}</div>'
        
        list_items.append(f'<div style="margin:8px 0; line-height:1.4;">{title_html}{metadata_html}</div>')
    
    return "".join(list_items)


def build_html(tz, events: List[Dict], due_today: List[Dict], due_tomorrow: List[Dict]) -> str:
    """
    Build the complete HTML content for the daily agenda email.
    
    This is the main function that combines calendar events and Notion tasks
    into a formatted HTML email body. It handles:
    - Separating all-day vs timed events
    - Detecting event overlaps and tight gaps
    - Formatting everything into readable sections
    
    Args:
        tz: Timezone object for date formatting
        events (List[Dict]): Calendar events for the day
        due_today (List[Dict]): Notion tasks due today
        due_tomorrow (List[Dict]): Notion tasks due tomorrow
        
    Returns:
        str: Complete HTML content for the email body
    """
    # Separate all-day events from timed events
    # All-day events are displayed separately at the top
    all_day_events = [e for e in events if e.get("all_day")]
    timed_events = [e for e in events if not e.get("all_day")]

    # Detect overlapping events (only for timed events)
    # This helps highlight scheduling conflicts
    num_timed = len(timed_events)
    overlapped = [False] * num_timed
    
    for i in range(num_timed):
        for j in range(i):
            # Check if events i and j overlap in time
            event_i_start = timed_events[i]["start"]
            event_i_end = timed_events[i]["end"]
            event_j_start = timed_events[j]["start"]
            event_j_end = timed_events[j]["end"]
            
            if (event_i_start < event_j_end) and (event_j_start < event_i_end):
                overlapped[i] = overlapped[j] = True

    # Generate the day label for the header
    now_local = datetime.now(tz)
    if events:
        day_label = events[0]["start"].strftime("%A, %B %-d")
    else:
        day_label = now_local.strftime("%A, %B %-d")

    # Render all-day events section
    if all_day_events:
        all_day_items = []
        for event in all_day_events:
            title = html.escape(event["title"])
            calendar = html.escape(event["calendar"])
            location = html.escape(event.get("location", ""))
            
            # Calendar pill
            pill_html = f'<span style="background:#f3f4f6; color:#6b7280; padding:2px 8px; border-radius:12px; font-size:12px; margin-right:8px;">{calendar}</span>'
            
            item_html = f'{pill_html}<strong style="color:#111827;">{title}</strong>'
            if location:
                item_html += f' <span style="color:#6b7280;">· {location}</span>'
            
            all_day_items.append(f'<div style="margin:8px 0; line-height:1.4;">{item_html}</div>')
        
        all_day_html = "".join(all_day_items)
    else:
        all_day_html = '<p style="color:#666; margin:8px 0;">None</p>'

    # Render timed events as a clean schedule table
    if timed_events:
        schedule_rows = []
        
        for i, event in enumerate(timed_events):
            title = html.escape(event["title"])
            calendar = html.escape(event["calendar"])
            location = html.escape(event.get("location", ""))
            notes = html.escape(event.get("notes", ""))
            
            # Truncate notes to first few words
            if notes:
                words = notes.split()
                if len(words) > 6:
                    notes = " ".join(words[:6]) + "..."
            
            # Format the time range
            start_time = _fmt_time(event["start"])
            end_time = _fmt_time(event["end"])
            time_range = f"{start_time}-{end_time}"
            
            # Build the event details with calendar pill
            pill_html = f'<span style="background:#f3f4f6; color:#6b7280; padding:2px 8px; border-radius:12px; font-size:12px; margin-left:8px;">{calendar}</span>'
            event_html = f'<strong style="color:#111827;">{title}</strong>{pill_html}'
            
            # Add overlap warning if this event conflicts with others
            if overlapped[i]:
                event_html += ' <span style="color:#dc2626; background:#fef2f2; padding:2px 6px; border-radius:8px; font-size:11px; font-weight:600;">⚠ overlap</span>'
            
            # Check for tight gaps with the next event
            if i < len(timed_events) - 1:
                next_event = timed_events[i + 1]
                gap_minutes = minutes_between(event["end"], next_event["start"])
                if 0 < gap_minutes < 15:  # Less than 15 minutes between events
                    event_html += f' <span style="color:#dc2626; font-size:12px;">• only {gap_minutes} min gap</span>'
            
            # Add location and notes
            details = []
            if location:
                details.append(f'<span style="color:#6b7280;">{location}</span>')
            if notes:
                details.append(f'<span style="color:#9ca3af; font-size:13px;">{notes}</span>')
            
            if details:
                event_html += f'<div style="margin-top:4px;">{" · ".join(details)}</div>'
            
            # Create the table row
            row_html = f'''
        <tr>
          <td style="white-space:nowrap; padding:12px 16px 12px 0; vertical-align:top; color:#6b7280; font-size:13px; font-weight:500;">{time_range}</td>
          <td style="padding:12px 0; line-height:1.4;">
            {event_html}
          </td>
        </tr>'''
            schedule_rows.append(row_html)
        
        schedule_html = f'<table style="width:100%; border-collapse:collapse;">{"".join(schedule_rows)}</table>'
    else:
        schedule_html = '<p style="color:#666; margin:8px 0;">No scheduled events</p>'

    # Combine everything into the final HTML with modern, calm design
    # This creates a clean email-friendly layout optimized for all major email clients
    html_content = f"""
    <div style="background-color:#f8fafc; padding:24px; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
      <div style="max-width:720px; margin:0 auto; background:#ffffff; border-radius:8px; padding:24px; box-shadow:0 1px 3px rgba(0,0,0,0.1);">
        
        <h2 style="margin:0 0 24px 0; font-size:20px; font-weight:600; color:#111827; line-height:1.3;">
          Today's agenda - {day_label}
        </h2>

        <div style="margin-bottom:32px;">
          <h3 style="margin:0 0 12px 0; font-size:16px; font-weight:500; color:#374151;">All-day today</h3>
          {all_day_html}
        </div>

        <div style="margin-bottom:32px;">
          <h3 style="margin:0 0 16px 0; font-size:16px; font-weight:500; color:#374151;">Schedule</h3>
          {schedule_html}
        </div>

        <div style="margin-bottom:32px;">
          <h3 style="margin:0 0 12px 0; font-size:16px; font-weight:500; color:#374151;">Due today</h3>
          {_render_due_list(due_today)}
        </div>

        <div style="margin-bottom:24px;">
          <h3 style="margin:0 0 12px 0; font-size:16px; font-weight:500; color:#374151;">Due tomorrow</h3>
          {_render_due_list(due_tomorrow)}
        </div>

        <p style="color:#9ca3af; margin:16px 0 0 0; font-size:12px; line-height:1.4;">
          Overlap warnings and tight gaps (&lt;15 min) apply to timed events only.
        </p>
        
      </div>
    </div>
    """
    
    return html_content
