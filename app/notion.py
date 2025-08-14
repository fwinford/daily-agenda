"""
Notion API Integration Module

This module handles all interactions with the Notion API:
- Converting Notion property types to readable text
- Fetching database titles
- Querying databases for tasks due on specific dates
- Handling relation fields and linked pages

Key features:
- Supports multiple property types (text, select, people, relations, etc.)
- Automatically resolves relation fields to show actual page titles
- Handles pagination for large databases
- Graceful error handling for API failures
"""

from datetime import datetime, timedelta
from typing import Dict, List
import requests

def _prop_to_text(prop, token=None) -> str:
    """
    Convert Notion property payloads into human-readable text.
    
    This function handles all the common Notion property types and converts
    them into simple strings that can be displayed in the agenda.
    
    Args:
        prop (dict): The property object from Notion API
        token (str, optional): Notion API token for fetching relation data
        
    Returns:
        str: Human-readable text representation of the property
        
    Supported property types:
    - title: Page titles
    - rich_text: Formatted text content
    - select: Single selection values
    - multi_select: Multiple selection values (comma-separated)
    - people: User names (comma-separated)
    - relation: Links to other pages (fetches actual titles if token provided)
    - url/email/phone_number: Direct text values
    """
    if not isinstance(prop, dict) or "type" not in prop:
        return ""
    
    t = prop["type"]
    
    # Handle title properties (usually the page name)
    if t == "title":
        return "".join(span.get("plain_text", "") for span in prop.get("title", []))
    
    # Handle rich text properties (formatted text content)
    if t == "rich_text":
        return "".join(span.get("plain_text", "") for span in prop.get("rich_text", []))
    
    # Handle single select properties (dropdown selections)
    if t == "select":
        return (prop.get("select") or {}).get("name", "") or ""
    
    # Handle multi-select properties (multiple tags/categories)
    if t == "multi_select":
        return ", ".join(tag.get("name", "") for tag in prop.get("multi_select", []))
    
    # Handle people properties (user assignments)
    if t == "people":
        return ", ".join(p.get("name") or p.get("id", "") for p in prop.get("people", []))
    
    # Handle relation properties (links to other database pages)
    if t == "relation":
        relations = prop.get("relation", [])
        if relations and token:
            # Fetch the actual titles of the related pages
            # This makes relations much more useful by showing "CS 101" instead of just "1 linked item"
            titles = []
            for rel in relations[:3]:  # Limit to first 3 to avoid too many API calls
                page_id = rel.get("id")
                if page_id:
                    try:
                        # Fetch the related page to get its title
                        resp = requests.get(
                            f"https://api.notion.com/v1/pages/{page_id}",
                            headers={
                                "Authorization": f"Bearer {token}",
                                "Notion-Version": "2022-06-28"
                            },
                            timeout=10
                        )
                        if resp.status_code == 200:
                            page_data = resp.json()
                            # Extract title from the page properties
                            page_props = page_data.get("properties", {})
                            for prop_value in page_props.values():
                                if prop_value.get("type") == "title":
                                    title = "".join(t.get("plain_text", "") for t in prop_value.get("title", []))
                                    if title:
                                        titles.append(title)
                                        break
                    except:
                        pass  # Ignore errors fetching individual pages
            
            # Build the final text representation
            if titles:
                result = ", ".join(titles)
                if len(relations) > len(titles):
                    result += f" (+{len(relations) - len(titles)} more)"
                return result
            elif relations:
                return f"{len(relations)} linked item(s)"
        return ""
    
    # Handle direct text properties
    if t in ("url","email","phone_number"):
        return prop.get(t) or ""
    
    return ""

def get_db_title(token: str, db_id: str) -> str:
    """
    Fetch a Notion database's title for display purposes.
    
    This provides a nice human-readable name for databases instead of just
    showing the database ID in the agenda.
    
    Args:
        token (str): Notion API token
        db_id (str): Database ID to fetch title for
        
    Returns:
        str: Database title or "Notion DB" if fetch fails
    """
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
    Query all configured databases for tasks/items due on a specific date.
    
    This is the main function that fetches your daily tasks from Notion.
    It goes through each database configured in config.yaml and finds
    items where the date property matches the given date.
    
    Args:
        token (str): Notion API token for authentication
        db_map (Dict[str, Dict]): Database configuration mapping from config.yaml
                                 Format: {db_id: {date_property, fields, name}}
        date_obj: Date object to query for (usually today or tomorrow)
        
    Returns:
        List[Dict]: List of tasks/items due on the date, each containing:
                   - title: Item title
                   - url: Direct link to the Notion page
                   - notes: Content from Notes field (if present)
                   - db_name: Human-readable database name
                   - fields: Dictionary of extra fields (Priority, Type, etc.)
    """
    # Early return if no token or database configuration
    if not token or not db_map:
        return []
    
    # Set up API headers for all requests
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    
    # Convert date to ISO format for Notion API
    iso_day = date_obj.strftime("%Y-%m-%d")
    out = []

    # Query each configured database
    for db_id, cfg in db_map.items():
        # Get database-specific configuration
        date_prop = cfg.get("date_property") or "Date"  # Which field contains the due date
        wanted    = cfg.get("fields") or []              # Extra fields to include
        db_name   = cfg.get("name") or get_db_title(token, db_id)  # Display name

        # Get database schema to determine property type
        try:
            db_resp = requests.get(f"https://api.notion.com/v1/databases/{db_id}", 
                                 headers=headers, timeout=30)
            db_resp.raise_for_status()
            db_info = db_resp.json()
            properties = db_info.get("properties", {})
            
            prop_info = properties.get(date_prop, {})
            prop_type = prop_info.get("type", "date")  # Default to date
            
        except:
            prop_type = "date"  # Fallback to date type
        
        # Build the Notion API query based on property type
        if prop_type == "created_time":
            # For created_time properties, query by creation date range
            # Use a tight 24-hour window to avoid overlaps between days
            start_of_day = f"{iso_day}T00:00:00.000-04:00"  # Eastern Time
            end_of_day = f"{iso_day}T23:59:59.999-04:00"
            
            payload = {
                "filter": {
                    "and": [
                        {
                            "property": date_prop,
                            "created_time": {
                                "on_or_after": start_of_day
                            }
                        },
                        {
                            "property": date_prop,
                            "created_time": {
                                "on_or_before": end_of_day
                            }
                        }
                    ]
                },
                "sorts": [{"property": date_prop, "direction": "ascending"}],
                "page_size": 100
            }
        else:
            # For regular date properties, use exact match
            payload = {
                "filter": {"property": date_prop, "date": {"equals": iso_day}},
                "sorts": [{"property": date_prop, "direction": "ascending"}],
                "page_size": 100
            }

        # Handle pagination (Notion returns results in pages)
        start_cursor = None
        while True:
            if start_cursor:
                payload["start_cursor"] = start_cursor
                
            # Make the API request
            resp = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query",
                                 headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            # Process each page/item returned
            for page in data.get("results", []):
                props = page.get("properties", {})
                
                # Extract the page title (usually the task name)
                title = "(Untitled)"
                for p in props.values():
                    if p.get("type") == "title":
                        if p["title"]:
                            title = "".join(t.get("plain_text","") for t in p["title"]) or "(Untitled)"
                        break
                
                # Extract notes if present (rich text field)
                notes = ""
                if "Notes" in props and props["Notes"]["type"] == "rich_text":
                    notes = "".join(t.get("plain_text","") for t in props["Notes"]["rich_text"])[:300]
                
                # Extract extra fields specified in config (Priority, Type, etc.)
                fields = {}
                for name in wanted:
                    if name in props:
                        fields[name] = _prop_to_text(props[name], token)

                # Build the final task object
                out.append({
                    "title": title,
                    "url": page.get("url"),
                    "notes": notes,
                    "db_name": db_name,
                    "fields": fields,
                })

            # Check if there are more pages to fetch
            if not data.get("has_more"):
                break
            start_cursor = data.get("next_cursor")

    return out