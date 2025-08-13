from datetime import datetime, timedelta
from typing import Dict, List
import requests, html

def _prop_to_text(prop) -> str:
    """Convert common Notion property payloads into readable text."""
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
    if t in ("url","email","phone_number"):
        return prop.get(t) or ""
    return ""

def get_db_title(token: str, db_id: str) -> str:
    """Fetch a Notion DB's title (nice label); fall back if anything fails."""
    try:
        r = requests.get(
            f"https://api.notion.com/v1/databases/{db_id}",
            headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"},
            timeout=20
        )
        r.raise_for_status()
        data = r.json()
        return "".join(t.get("plain_text", "") for t in data.get("title", [])) or "Notion DB"
    except Exception:
        return "Notion DB"

def query_due_on(token: str, db_map: Dict[str, Dict], date_obj) -> List[Dict]:
    """
    For each DB in db_map, fetch pages whose date_property equals date_obj.
    db_map[db_id] = {date_property: str, fields: [..], name: optional override}
    Returns: [{title,url,notes,db_name,fields:{...}}]
    """
    if not token or not db_map:
        return []
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    iso_day = date_obj.strftime("%Y-%m-%d")
    out = []

    for db_id, cfg in db_map.items():
        date_prop = cfg.get("date_property") or "Date"
        wanted    = cfg.get("fields") or []
        db_name   = cfg.get("name") or get_db_title(token, db_id)

        payload = {
            "filter": {"property": date_prop, "date": {"equals": iso_day}},
            "sorts": [{"property": date_prop, "direction": "ascending"}],
            "page_size": 100
        }

        start_cursor = None
        while True:
            if start_cursor:
                payload["start_cursor"] = start_cursor
            resp = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query",
                                 headers=headers, json=payload, timeout=30)
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
                # notes
                notes = ""
                if "Notes" in props and props["Notes"]["type"] == "rich_text":
                    notes = "".join(t.get("plain_text","") for t in props["Notes"]["rich_text"])[:300]
                # extra fields
                fields = {}
                for name in wanted:
                    if name in props:
                        fields[name] = _prop_to_text(props[name])

                out.append({
                    "title": title,
                    "url": page.get("url"),
                    "notes": notes,
                    "db_name": db_name,
                    "fields": fields,
                })

            if not data.get("has_more"):
                break
            start_cursor = data.get("next_cursor")

    return out