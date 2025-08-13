from typing import List, Dict
from datetime import datetime
import html

def minutes_between(a_end, b_start):
    """Integer minutes from a_end to b_start (can be negative)."""
    return int((b_start - a_end).total_seconds() // 60)

def _fmt_time(dt: datetime) -> str:
    """Portable-ish time formatting; adjust for Windows if needed."""
    try:
        return dt.strftime("%-I:%M %p")  # macOS/Linux
    except ValueError:
        return dt.strftime("%#I:%M %p")  # Windows

def _render_due_list(items: List[Dict]) -> str:
    if not items:
        return "<p>Nothing due 🎉</p>"

    def render_fields(d):
        pairs = [f"{html.escape(k)}: {html.escape(v)}" for k, v in d.items() if v]
        return " · ".join(pairs)

    lis = []
    for x in items:
        meta = []
        if x.get("db_name"):
            meta.append(f"<span style='color:#666;'>[{html.escape(x['db_name'])}]</span>")
        if x.get("fields"):
            fs = render_fields(x["fields"])
            if fs:
                meta.append(fs)
        meta_str = " — " + " · ".join(meta) if meta else ""
        notes_str = f" — <span style='color:#555;'>{html.escape(x['notes'])}</span>" if x.get("notes") else ""
        lis.append(f'<li><a href="{html.escape(x["url"])}">{html.escape(x["title"])}</a>{meta_str}{notes_str}</li>')
    return "<ul>" + "".join(lis) + "</ul>"

def build_html(tz, events: List[Dict], due_today: List[Dict], due_tomorrow: List[Dict]) -> str:
    """
    Render:
      1) All-day events (header list)
      2) Timed schedule (table) with tight-gap & overlap flags (all-day excluded)
      3) Due today / Due tomorrow lists (with db name + fields)
    """
    # split out all-day items
    all_day = [e for e in events if e.get("all_day")]
    timed   = [e for e in events if not e.get("all_day")]

    # overlap flags (timed only)
    n = len(timed)
    overlapped = [False] * n
    for i in range(n):
        for j in range(i):
            if (timed[i]["start"] < timed[j]["end"]) and (timed[j]["start"] < timed[i]["end"]):
                overlapped[i] = overlapped[j] = True

    # day label
    now_local = datetime.now(tz)
    day_label = (events[0]["start"].strftime("%A, %B %-d")
                 if events else now_local.strftime("%A, %B %-d"))

    # all-day list
    if all_day:
        ad_items = "".join(
            f"<li><strong>{html.escape(e['title'])}</strong> <span style='color:#666;'>({html.escape(e['calendar'])})</span>"
            f"{' · ' + html.escape(e['location']) if e.get('location') else ''}</li>"
            for e in all_day
        )
        all_day_html = f"<ul>{ad_items}</ul>"
    else:
        all_day_html = "<p>None</p>"

    # timed schedule
    rows = []
    prev_end = None
    for idx, e in enumerate(timed):
        time_cell = f"{_fmt_time(e['start'])}–{_fmt_time(e['end'])}"
        gap = ""
        if prev_end:
            gap_min = minutes_between(prev_end, e["start"])
            if 0 <= gap_min < 15:
                gap = f' <span style="color:#c00;">• only {gap_min} min gap</span>'
        overlap = ' <span style="color:#c00;">⚠︎ overlaps</span>' if overlapped[idx] else ""
        cal_label = html.escape(e.get("calendar","Calendar"))

        rows.append(f"""
        <tr>
          <td style="white-space:nowrap;padding:6px 10px;vertical-align:top;">{time_cell}</td>
          <td style="padding:6px 0;">
            <strong>{html.escape(e['title'])}</strong>
            <span style="color:#666;">({cal_label})</span>{overlap}
            {' · ' + html.escape(e['location']) if e.get('location') else ''}
            {f'<div style="color:#555;font-size:12px;margin-top:2px;">{html.escape(e.get("notes","")[:200])}</div>' if e.get('notes') else ''}
          </td>
        </tr>
        """)
        prev_end = e["end"]

    schedule_html = ("<table cellpadding='0' cellspacing='0' style='width:100%;border-collapse:collapse;'>"
                     + "".join(rows) + "</table>") if rows else "<p>No timed events.</p>"

    # final compose
    return f"""
    <div style="font:14px/1.5 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial; max-width:760px;">
      <h2 style="margin:0 0 12px;">Today’s agenda — {day_label}</h2>

      <h3>All-day today</h3>
      {all_day_html}

      <h3 style="margin-top:16px;">Schedule</h3>
      {schedule_html}

      <h3 style="margin-top:18px;">Due today</h3>
      {_render_due_list(due_today)}

      <h3 style="margin-top:18px;">Due tomorrow</h3>
      {_render_due_list(due_tomorrow)}

      <p style="color:#777;margin-top:16px;">Tight-gap flag = &lt;15 min; overlaps apply only to timed events.</p>
    </div>
    """