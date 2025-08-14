#!/usr/bin/env python3
"""
Debug script for testing daily agenda functionality
This script provides debugging features like preview-only mode and date override
without cluttering the main production code.

Usage:
    python debug.py --preview-only                    # Preview today's agenda
    python debug.py --date 2025-08-14 --preview-only  # Preview specific date
    python debug.py --date 2025-08-14                 # Send email for specific date
"""

import argparse
import tempfile
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path so we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))
from main import run_once

def main():
    """Debug entry point with preview and date override capabilities"""
    parser = argparse.ArgumentParser(description="Debug daily agenda generation")
    parser.add_argument("--preview-only", action="store_true", 
                       help="Generate HTML preview without sending email")
    parser.add_argument("--date", type=str, 
                       help="Generate agenda for specific date (YYYY-MM-DD format)")
    
    args = parser.parse_args()
    
    # Parse target date if provided
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print("Error: Invalid date format. Please use YYYY-MM-DD format.")
            exit(1)
    
    # Run with debugging features
    html = run_once(target_date, preview_only=args.preview_only)
    
    if args.preview_only:
        # Save HTML preview to temp file for debugging
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, dir='.') as f:
            f.write(html)
            preview_file = f.name
        
        print(f"HTML preview saved to: {preview_file}")
        print("Open this file in your browser to preview the email")
        print("Debug mode: Email not sent")

if __name__ == "__main__":
    main()
