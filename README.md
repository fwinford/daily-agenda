# Daily Agenda Email System

**Get your daily schedule delivered to your inbox automatically!**

This app combines your calendar events and Notion tasks into one beautiful daily agenda email.

## What You'll Get

Every morning, you'll receive an email with:  
✮ **Today's calendar events** (from iCloud, Google Calendar, etc.)  
✮ **Tasks due today & tomorrow** (from your Notion databases)  
✮ **Professional HTML formatting**  

## Project Structure

```
daily-agenda/
├── app/                    # Core application modules
│   ├── __init__.py
│   ├── calendars.py        # Calendar/ICS fetching
│   ├── emailer.py          # Email sending
│   ├── notion.py           # Notion API integration
│   └── render.py           # HTML email rendering
├── config/                 # Configuration files
│   ├── .env               # Environment variables (create from .env.example)
│   ├── .env.example       # Template file
│   ├── config.yaml        # Database configuration
│   └── config.yaml.example # Template
├── scripts/                # Utility & debug scripts
│   ├── debug.py           # Preview & date override tools
│   ├── test_calendar.py   # Calendar URL testing
│   └── test_simple.py     # Basic setup verification
├── tests/                  # Unit tests
├── main.py                 # Main application entry point
├── run_tests.py           # Test runner
└── requirements.txt       # Python dependencies
```

## Features

✮ **Automatic daily emails** with your personalized agenda  
✮ **Multiple calendar support** (iCloud, Google, Outlook, etc.)  
✮ **Notion database integration** with custom fields  
✮ **Preview mode** to test without sending emails  
✮ **Secure authentication** with app passwords  
✮ **Built-in testing** to verify everything works  

## Quick Start

```bash
# 1. Get the code
git clone https://github.com/fwinford/daily-agenda
cd daily-agenda

# 2. Set up Python
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Copy and edit your settings
cp config/.env.example config/.env
# Edit config/.env with your details (see setup guide below)

# 4. Test it works
python scripts/test_simple.py

# 5. Send yourself a test email
python main.py
```

## Setup Instructions

### 1. Install Dependencies

```bash
git clone https://github.com/fwinford/daily-agenda
cd daily-agenda
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
cp config/.env.example config/.env
```

Edit `config/.env` with your information:

```bash
TO_EMAIL="your@email.com"
SMTP_HOST="smtp.gmail.com"          # Gmail settings
SMTP_PORT="465"
SMTP_USER="your@gmail.com"
SMTP_PASS="your_app_password"       # See Gmail setup below
TIMEZONE="America/New_York"         # Your local timezone
ICS_URLS="https://your-calendar-url.ics"
NOTION_TOKEN="your_notion_token"    # See Notion setup below
```

⚠ **Important**: Use app passwords for email, not your main password

### 3. Set Up Notion Integration

1. **Create integration**: Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. **New integration** → Name it "daily agenda" → Copy the token
3. **Get database ID**: From your database URL: `notion.so/DATABASE_ID?v=...`
4. **Share databases**: In each database, click "..." → "Connections" → Connect your integration

Edit `config/config.yaml`:

```yaml
databases:
  "YOUR_DATABASE_ID":
    name: "Tasks"                    # Optional friendly name
    date_property: "Due Date"        # Required: your date column name
    fields: ["Priority", "Status"]   # Optional: extra fields to show
```

**Common date property names**: "Due Date", "Deadline", "Date", "Due"

### 4. Set Up Email Authentication

**For Gmail**:
1. Enable 2-factor authentication
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Generate app password for "daily agenda"
4. Use this 16-character password as `SMTP_PASS`

**Other providers**:
✮ **Outlook**: `smtp-mail.outlook.com:587`
✮ **Yahoo**: `smtp.mail.yahoo.com:587`

### 5. Get Calendar URLs

**iCloud Calendars**:
1. Calendar app → Right-click calendar → "Share Calendar" → "Public"
2. Copy webcal URL and change `webcal://` to `https://`

**Google Calendars**:
1. Google Calendar settings → Your calendar → "Integrate Calendar" 
2. Copy "Secret address in iCal format"

**Multiple calendars**: Separate URLs with commas in `.env` file

### 6. Test Your Setup

```bash
python scripts/test_simple.py      # Basic verification
python scripts/debug.py --preview-only  # Preview without sending
python main.py                     # Send test email
```

## Usage

**Run once**:
```bash
python main.py
```

**Automate daily at 7 AM**:

Linux/Mac (crontab):
```bash
crontab -e
# Add this line (replace /full/path/to with your actual path):
0 7 * * * cd /full/path/to/daily-agenda && /full/path/to/daily-agenda/.venv/bin/python main.py
```

Windows (Task Scheduler):
1. Open Task Scheduler → Create Basic Task
2. Set trigger for daily 7 AM
3. Action: Start a program
4. Program: `C:\full\path\to\daily-agenda\.venv\Scripts\python.exe`
5. Arguments: `main.py`
6. Start in: `C:\full\path\to\daily-agenda`

## Development & Testing

```bash
python run_tests.py                          # Run all tests
python scripts/debug.py --preview-only       # Preview without sending
python scripts/debug.py --date 2025-08-14 --preview-only  # Test specific date
python scripts/test_calendar.py              # Test calendar URLs
```

## Troubleshooting

**Email Issues**:
✗ **401 unauthorized** → Use app password, not main password
✗ **Timeout** → Try port 465 (SSL) instead of 587 (TLS)

**Notion Issues**:
✗ **401/403 errors** → Share databases with your integration
✗ **Empty fields** → Check field names match exactly in `config/config.yaml`

**Calendar Issues**:
✗ **No events** → Verify ICS URLs are public and accessible
✗ **Wrong timezone** → Check `TIMEZONE` setting in `config/.env`

## Example Output

```
Today's Agenda - Wednesday, Aug 13

Calendar Events:
* 9:00 AM - 10:00 AM: Team Meeting (Conference Room A)
* 12:00 PM - 1:30 PM: Lunch with Client (Restaurant XYZ)

Due Today:
* Submit Application (Tech Corp - Full-time)

Due Tomorrow:  
* CS 101 Homework (Computer Science - Assignment)
* Project Proposal (Business Strategy - Essay)
```

## Security Notes

⚠ **Never commit `config/.env`** - it contains secrets
⚠ **Use app passwords** for email (not your main password)  
⚠ **Keep Notion tokens secure** - they access your databases

## Advanced Configuration

**Add database fields**: Edit `fields` array in `config/config.yaml`
**Change email template**: Edit `app/render.py`
**Add calendar sources**: Add ICS URLs to `.env` (comma-separated)
**Common timezones**: `America/New_York`, `Europe/London`, `Asia/Tokyo`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality  
4. Run the test suite
5. Submit a pull request

## License

This project is open source. Feel free to use and modify as needed.
