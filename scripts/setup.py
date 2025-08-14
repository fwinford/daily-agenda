#!/usr/bin/env python3
"""
Comprehensive setup script for daily agenda system
Validates configuration, dependencies, and tests connections
This replaces and consolidates the old validate_setup.py
"""

import os
import sys
import yaml
import requests
from pathlib import Path
from dotenv import load_dotenv

def check_dependencies():
    """Check if all required packages are installed"""
    print("Checking dependencies...")
    try:
        import requests
        import yaml
        import pytz
        import icalendar
        from dotenv import load_dotenv
        from bs4 import BeautifulSoup
        print("All dependencies installed")
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists and has required variables"""
    print("Checking .env file...")
    env_path = Path("config/.env")
    if not env_path.exists():
        print("config/.env file not found!")
        print("Copy config/.env.example to config/.env and configure your settings")
        return False
    
    load_dotenv(env_path)
    
    required_vars = [
        "TO_EMAIL", "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS",
        "TIMEZONE", "ICS_URLS", "NOTION_TOKEN"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.strip() == "":
            missing_vars.append(var)
    
    if missing_vars:
        print(f"Missing or empty environment variables: {', '.join(missing_vars)}")
        return False
    
    print(".env file configured correctly")
    return True

def check_config_yaml():
    """Check if config.yaml exists and is properly configured"""
    print("Checking config.yaml...")
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        print("config/config.yaml not found!")
        print("Copy config/config.yaml.example to config/config.yaml and configure your databases")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if not config or not config.get('databases'):
            print("config.yaml missing databases configuration")
            return False
            
        print(f"config.yaml configured with {len(config['databases'])} database(s)")
        
        # Show configured databases
        for db_id, db_config in config['databases'].items():
            name = db_config.get('name', 'Unknown')
            print(f"   - {name} ({db_id[:8]}...)")
        
        return True
    except Exception as e:
        print(f"Error reading config.yaml: {e}")
        return False

def test_ics_urls():
    """Test ICS calendar URLs"""
    print("Testing calendar URLs...")
    ics_urls = os.getenv("ICS_URLS", "").split(",")
    working_urls = 0
    
    for i, url in enumerate(ics_urls):
        url = url.strip()
        if not url:
            continue
            
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200 and 'BEGIN:VCALENDAR' in response.text:
                print(f"Calendar {i+1}: Working (contains calendar data)")
                working_urls += 1
            elif response.status_code == 200:
                print(f"Calendar {i+1}: HTTP 200 but no calendar data")
            else:
                print(f"Calendar {i+1}: HTTP {response.status_code}")
        except Exception as e:
            print(f"Calendar {i+1}: {str(e)[:50]}...")
    
    total_urls = len([u for u in ics_urls if u.strip()])
    if working_urls > 0:
        print(f"{working_urls}/{total_urls} calendars working")
        return True
    else:
        print("No working calendar URLs found")
        return False

def test_notion_connection():
    """Test Notion API connection"""
    print("Testing Notion connection...")
    token = os.getenv("NOTION_TOKEN")
    if not token:
        print("NOTION_TOKEN not set")
        return False
    
    # Test with a simple API call
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get("https://api.notion.com/v1/users/me", headers=headers, timeout=10)
        if response.status_code == 200:
            print("Notion API connection working")
            return True
        else:
            print(f"Notion API error: {response.status_code}")
            if response.status_code == 401:
                print("   Check your NOTION_TOKEN is correct")
            return False
    except Exception as e:
        print(f"Notion connection failed: {e}")
        return False

def test_email_config():
    """Test email configuration (without actually sending)"""
    print("Checking email configuration...")
    
    required_email_vars = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "TO_EMAIL"]
    for var in required_email_vars:
        if not os.getenv(var):
            print(f"{var} not configured")
            return False
    
    smtp_host = os.getenv("SMTP_HOST")
    smtp_user = os.getenv("SMTP_USER")
    to_email = os.getenv("TO_EMAIL")
    
    print(f"Email configured: {smtp_user} -> {to_email} via {smtp_host}")
    print("   (Note: Not actually sending test email)")
    return True

def main():
    """Run complete setup validation"""
    print("Daily Agenda Setup Validation", flush=True)
    print("=" * 40, flush=True)
    
    # Change to project root directory
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    os.chdir(project_dir)
    
    # Run all validation checks
    checks = [
        ("Dependencies", check_dependencies),
        ("Environment", check_env_file),
        ("Configuration", check_config_yaml),
        ("Calendars", test_ics_urls),
        ("Notion API", test_notion_connection),
        ("Email Config", test_email_config),
    ]
    
    passed_checks = 0
    total_checks = len(checks)
    
    for name, check_func in checks:
        if check_func():
            passed_checks += 1
        print()  # Add spacing between checks
    
    print("=" * 40)
    print(f"Results: {passed_checks}/{total_checks} checks passed")
    
    if passed_checks == total_checks:
        print("All checks passed! Your setup is ready.")
        print("\nNext steps:")
        print("  python main.py                          # Send today's agenda")
        print("  python scripts/debug.py --preview-only  # Preview without sending")
        print("  python run_tests.py                     # Run unit tests")
        return 0
    else:
        print("Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
