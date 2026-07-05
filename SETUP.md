# setup guide

This guide walks through setting up Daily Agenda with email, calendar feeds, and Notion tasks.

## 1. clone the repo

```bash
git clone https://github.com/fwinford/daily-agenda
cd daily-agenda
```

## 2. set up python

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

On Windows:

```bash
.venv\Scripts\activate
```

## 3. create config files

```bash
cp config/.env.example config/.env
cp config/config.yaml.example config/config.yaml
```

## 4. configure environment variables

Edit `config/.env`:

```env
TO_EMAIL="your@email.com"
SMTP_HOST="smtp.gmail.com"
SMTP_PORT="465"
SMTP_USER="your@gmail.com"
SMTP_PASS="your_app_password"
TIMEZONE="America/New_York"
ICS_URLS="https://your-calendar-url.ics"
NOTION_TOKEN="your_notion_token"
```

Use app passwords for email, not your main email password.

## 5. set up notion

1. Go to Notion integrations.
2. Create a new integration.
3. Copy the integration token into `NOTION_TOKEN`.
4. Open the Notion database you want to use.
5. Share the database with your integration.
6. Copy the database ID from the database URL.

Then edit `config/config.yaml`:

```yaml
databases:
  "YOUR_DATABASE_ID":
    name: "Tasks"
    date_property: "Due Date"
    fields: ["Priority", "Status"]
```

The `date_property` should match the exact name of your Notion due date column.

## 6. get calendar urls

### google calendar

1. Open Google Calendar settings.
2. Select your calendar.
3. Go to “Integrate calendar.”
4. Copy the secret iCal address.
5. Add it to `ICS_URLS`.

### icloud calendar

1. Open Calendar.
2. Share the calendar publicly.
3. Copy the `webcal://` link.
4. Change `webcal://` to `https://`.
5. Add it to `ICS_URLS`.

For multiple calendars, separate URLs with commas.

```env
ICS_URLS="https://calendar-one.ics,https://calendar-two.ics"
```

## 7. test the setup

Run a basic setup check:

```bash
python scripts/test_simple.py
```

Preview the agenda without sending an email:

```bash
python scripts/debug.py --preview-only
```

Send a test email:

```bash
python main.py
```

## 8. automate it

### mac/linux with cron

Open your crontab:

```bash
crontab -e
```

Add a line like this to run it every day at 7 AM:

```bash
0 7 * * * cd /full/path/to/daily-agenda && /full/path/to/daily-agenda/.venv/bin/python main.py
```

Replace `/full/path/to/daily-agenda` with the actual path to the repo.

### windows task scheduler

1. Open Task Scheduler.
2. Create a basic task.
3. Set the trigger to daily.
4. Set the action to start a program.
5. Use your virtual environment’s Python executable.
6. Set `main.py` as the argument.
7. Set the repo folder as the working directory.

## troubleshooting

### email issues

If email authentication fails, make sure you are using an app password instead of your main password.

If the email times out, try port `465` with SSL instead of port `587`.

### notion issues

If Notion returns a permissions error, make sure the database is shared with your integration.

If tasks are missing, check that the date property name in `config.yaml` matches your Notion database exactly.

### calendar issues

If no events appear, make sure the calendar URL is an accessible `.ics` link.

If event times look wrong, check the `TIMEZONE` value in `config/.env`.

## security notes

- never commit `config/.env`
- keep email app passwords private
- keep notion tokens private
- use `.env.example` for placeholder values only
