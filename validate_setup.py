#!/usr/bin/env python3
"""
Setup validation script for Daily Agenda
Run this after setting up your .env and config.yaml files
"""
import os
import sys
from dotenv import load_dotenv

def validate_setup():
    """Validate the setup configuration"""
    print("validating daily agenda setup")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_env = [
        "TO_EMAIL", "SMTP_HOST", "SMTP_PORT", "SMTP_USER", 
        "SMTP_PASS", "TIMEZONE", "NOTION_TOKEN"
    ]
    
    missing_env = []
    for var in required_env:
        value = os.getenv(var)
        if not value:
            missing_env.append(var)
        else:
            if var == "SMTP_PASS":
                print(f"✓ {var}: {'*' * len(value)}")
            elif var == "NOTION_TOKEN":
                print(f"✓ {var}: {value[:10]}...")
            else:
                print(f"✓ {var}: {value}")
    
    if missing_env:
        print(f"\n✕ missing environment variables: {', '.join(missing_env)}")
        print("please check your .env file")
        return False
    
    # Check config.yaml
    if not os.path.exists("config.yaml"):
        print("\n✕ config.yaml not found")
        return False
    
    try:
        import yaml
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
            
        if not config or "databases" not in config:
            print("\n✕ config.yaml missing 'databases' section")
            return False
            
        db_count = len(config["databases"])
        print(f"\n✓ config.yaml: {db_count} database(s) configured")
        
        for db_id, db_config in config["databases"].items():
            if db_id.startswith("YOUR_"):
                print(f"WARNING: database ID '{db_id}' looks like a placeholder")
                print("   please replace with your actual notion database ID")
                return False
            else:
                print(f"   - {db_config.get('name', 'unknown')}: {db_id[:8]}...")
                
                # Check required fields
                if not db_config.get("date_property"):
                    print(f"   WARNING: no 'date_property' specified for {db_config.get('name', db_id)}")
                    print("      please add the name of your date column")
                    return False
                
    except Exception as e:
        print(f"\n✕ error reading config.yaml: {e}")
        return False
    
    # Check calendar URLs
    ics_urls = os.getenv("ICS_URLS", "")
    if ics_urls:
        urls = [u.strip() for u in ics_urls.split(",") if u.strip()]
        print(f"\n✓ calendar URLs: {len(urls)} configured")
        for i, url in enumerate(urls, 1):
            print(f"   {i}. {url[:50]}{'...' if len(url) > 50 else ''}")
    else:
        print("\n⚠ no ICS_URLS configured (calendar events will be empty)")
    
    print("\n" + "✮" * 40)
    print("✓ setup validation complete!")
    print("\nnext steps:")
    print("1. run tests: ./.venv/bin/python run_tests.py")
    print("2. test the app: ./.venv/bin/python main.py")
    
    return True

if __name__ == "__main__":
    if not validate_setup():
        sys.exit(1)
