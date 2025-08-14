# Daily Agenda Email System

A Python application that automatically generates and emails a personalized daily agenda by combining:
- Calendar events from ICS feeds (like iCloud, Google Calendar)  
- Tasks and assignments from Notion databases
- Beautiful HTML email formatting

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
│   ├── config.yaml        # Database configuration
│   └── config.yaml.example # Template
├── scripts/                # Utility & debug scripts
│   ├── debug.py           # Preview & date override tools
│   ├── test_calendar.py   # Calendar URL testing utility
│   └── test_simple.py     # Basic setup verification
├── tests/                  # Unit tests
│   ├── test_calendars.py
│   ├── test_daily_agenda.py
│   ├── test_email.py
│   ├── test_main.py
│   └── test_notion.py
├── main.py                 # Main application entry point
├── run_tests.py           # Test runner
└── requirements.txt       # Python dependencies
```

## Quick Commands

```bash
# Normal operation
python main.py

# Development & testing
python run_tests.py                    # Run all unit tests
python scripts/debug.py --preview-only # Preview without sending email
python scripts/debug.py --date 2025-08-14 --preview-only # Test specific date
python scripts/test_simple.py          # Basic setup check
python scripts/test_calendar.py        # Test calendar URLs
```

## Features

+ **Multiple calendar support** via ICS URLs
+ **Notion integration** with custom database fields  
+ **Relation field support** (shows linked class names, etc.)
+ **Overlap detection** for conflicting calendar events
+ **Customizable fields** per database (Company, Class, Type, etc.)
+ **SSL/TLS email support** (Gmail, Outlook, etc.)
+ **Comprehensive testing** with unit tests
+ **Debug & preview tools** for development

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
git clone <https://github.com/fwinford/daily-agenda>
cd daily-agenda
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set up Environment Variables

Copy the example environment file and fill in your details:

```bash
cp config/.env.example config/.env
```

Edit `config/.env` with your information:

```bash
TO_EMAIL="your@email.com"
SMTP_HOST="smtp.gmail.com"
SMTP_PORT="465"
SMTP_USER="your@gmail.com"
SMTP_PASS="your_app_password"
TIMEZONE="America/New_York"
ICS_URLS="https://your-calendar-url-1.ics,https://your-calendar-url-2.ics"
NOTION_TOKEN="your_notion_integration_token"
```

### 3. Configure Your Notion Integration

#### Create a Notion Integration:
1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **"New integration"**
3. Name it something like "daily agenda"
4. Select your workspace
5. Copy the **"Internal Integration Token"**
6. Paste it as `NOTION_TOKEN` in your `.env` file

#### Get Your Database IDs:
1. Open your notion database in a web browser
2. Copy the URL - it looks like: `https://www.notion.so/YOUR_DATABASE_ID?v=...`
3. Extract the database ID (the long string between `/` and `?`)

#### Share Databases with Integration:
1. In each notion database, click the **"..."** menu (top right)
2. Click **"Connections"** → **"Connect to"** → select your integration

### 4. Configure Your Databases

Edit `config/config.yaml` with your database IDs and desired fields:

```yaml
databases:
  "YOUR_FIRST_DATABASE_ID":              # replace with actual notion database id
    name: "My Tasks"                     # optional: friendly name (auto-detected if not provided)
    date_property: "Due Date"            # required: name of your date property  
    fields: ["Priority", "Status"]       # optional: additional fields to show
  "YOUR_SECOND_DATABASE_ID":             # replace with actual notion database id
    name: "Projects"                     # optional: friendly name
    date_property: "Deadline"            # required: name of your date property
    fields: ["Category", "Owner"]        # optional: additional fields to show
```

**important notes:**
- **database_id**: get this from your notion database URL
- **date_property**: must match the exact name of your date column in notion
- **fields**: should match the exact names of properties in your notion database
- **name**: optional - if not provided, the system will auto-detect the database name

**common date property names:**
- "Due Date", "Deadline", "Date", "Due", "Scheduled", "Target Date"

**Field Types Supported:**
- Text fields
- Select/Multi-select fields
- Relation fields (shows linked page titles)
- People fields
- URL/Email/Phone fields

### 5. Set up Email Authentication

#### For Gmail:
1. **enable 2-factor authentication** on your gmail account
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Generate an app password for "daily agenda"
4. Use this 16-character password as `SMTP_PASS` in `.env`
5. Use these settings:
   ```
   SMTP_HOST="smtp.gmail.com"
   SMTP_PORT="465"
   ```

#### For Other Email Providers:
- **outlook**: `smtp-mail.outlook.com:587`
- **yahoo**: `smtp.mail.yahoo.com:587`
- check your provider's SMTP settings

### 6. Get Calendar ICS URLs

The system supports multiple calendar types and can combine events from all of them:

#### Apple/iCloud Calendars:
1. Open Calendar app on Mac/iOS
2. Right-click your calendar → **"Share Calendar"**
3. Make it **"Public"**
4. Copy the webcal URL and change `webcal://` to `https://`
5. **Multiple calendars**: You can add as many iCloud calendars as you want

Example iCloud URLs:
```
https://p108-caldav.icloud.com/published/2/MTY1ODU3MDgxNzQxNjU4Ne...
```

#### Google Calendars:
1. Open Google Calendar settings
2. Click on your calendar → **"Integrate Calendar"**
3. Copy the **"Secret address in iCal format"** (not the embed URL)
4. **Multiple Google calendars**: Each calendar has its own ICS URL

To convert a Google Calendar embed URL to ICS format:
- **From**: `https://calendar.google.com/calendar/embed?src=nyu.edu_85g8...&ctz=America%2FNew_York`
- **To**: `https://calendar.google.com/calendar/ical/nyu.edu_85g8.../public/basic.ics`

#### Adding Multiple Calendars:
In your `config/.env` file, separate multiple URLs with commas:
```bash
ICS_URLS="https://your-icloud-calendar1.ics,https://your-icloud-calendar2.ics,https://calendar.google.com/calendar/ical/your-google-cal/public/basic.ics"
```

#### Other Calendar Sources:
- **Outlook/Exchange**: Most provide ICS/webcal URLs in sharing settings
- **University calendars**: Often provide public ICS feeds
- **Any ICS feed**: The system works with any valid ICS URL

### 7. Timezone Configuration

**Important**: Set your local timezone in `config/.env` for accurate event times:

```bash
TIMEZONE="America/New_York"
```

**Common timezones:**
- `America/New_York` (Eastern Time)
- `America/Chicago` (Central Time) 
- `America/Denver` (Mountain Time)
- `America/Los_Angeles` (Pacific Time)
- `Europe/London` (GMT/BST)
- `Europe/Paris` (CET/CEST)
- `Asia/Tokyo` (JST)
- `Australia/Sydney` (AEST/AEDT)

**How timezone handling works:**
- All calendar events are converted to your local timezone
- All-day events are properly detected and displayed
- Notion due dates are interpreted in your local timezone
- Email timestamps use your timezone

**Finding your timezone:**
1. **Linux/Mac**: Run `timedatectl` or check `/etc/timezone`
2. **Python**: `python -c "import time; print(time.tzname)"`
3. **Online**: Search for "timezone database" + your city

### 8. Test Your Setup

```bash
# Run unit tests to verify components
python run_tests.py

# Test basic setup
python scripts/test_simple.py

# Preview without sending email
python scripts/debug.py --preview-only

# Test the full application (dry run)
python -c "
import main
cfg = main.load_config()
print('Config loaded successfully!')
print(f'Databases: {len(cfg[\"db_map\"])}')
print(f'ICS URLs: {len(cfg[\"ics_urls\"])}')
"

# Run the full application
python main.py
```

## usage

### Run Once
```bash
python main.py
```

### Automate with Cron (Linux/Mac)
add to your crontab to run daily at 7 AM:
```bash
crontab -e
# add this line:
0 7 * * * cd /path/to/daily-agenda && python main.py
```

### Automate with Task Scheduler (Windows)
1. open task scheduler
2. create a new task
3. set trigger for daily at 7 AM
4. set action to run: `C:\path\to\daily-agenda\.venv\Scripts\python.exe main.py`
5. set start in: `C:\path\to\daily-agenda`

## customization

### Adding New Database Fields
1. add the field name to the `fields` array in `config/config.yaml`
2. the system automatically detects field types and formats them

### Changing Email Template
edit `app/render.py` to customize the HTML email template.

### Adding New Calendar Sources
add ICS URLs to the `ICS_URLS` environment variable in `config/.env` (comma-separated).

### Timezone Configuration
set your timezone in `config/.env`:
```bash
TIMEZONE="America/New_York"  # or "Europe/London", "Asia/Tokyo", etc.
```

## Security Notes

- **never commit `config/.env`** - it contains secrets
- **use app passwords** for email (not your main password)
- **keep notion tokens secure** - they have access to your databases
- the `config/.env` file is already in `.gitignore`

## Troubleshooting

### Email Issues
- **x 401 unauthorized**: check if you're using an app password, not your main password
- **x timeout**: try port 465 (SSL) instead of 587 (TLS)
- **x "less secure apps"**: use app passwords instead

### Notion Issues
- **x 401/403 errors**: make sure you've shared your databases with the integration
- **x empty fields**: check that field names in `config/config.yaml` match exactly
- **x missing relations**: the system automatically fetches related page titles

### Calendar Issues
- **x no events**: verify your ICS URLs are public and accessible
- **x wrong timezone**: check the `TIMEZONE` setting in `config/.env`

## Example Output

your daily agenda email will look like:

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

## Contributing

1. fork the repository
2. create a feature branch
3. make your changes
4. add tests for new functionality
5. run the test suite
6. submit a pull request

## License

this project is open source. feel free to use and modify as needed.

---

**Happy organizing!**
