# daily agenda

daily agenda is a python automation tool that sends a daily email with your calendar events and notion tasks in one place.

i built it because my schedule was spread across too many systems, and i wanted one simple email every morning instead of checking calendar apps, notion pages, and task lists separately.

## what it does

- pulls events from calendar feeds like google calendar, icloud, and outlook
- pulls tasks from notion databases
- shows tasks due today and tomorrow
- renders everything into a clean html email
- supports preview mode so you can test without sending
- includes scripts for debugging calendar, notion, and email setup

## tech stack

- **language:** python
- **calendar:** ics / ical feeds
- **tasks:** notion api
- **email:** smtp
- **config:** dotenv, yaml
- **testing:** pytest

## running locally

```bash
git clone https://github.com/fwinford/daily-agenda
cd daily-agenda

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
cp config/.env.example config/.env
cp config/config.yaml.example config/config.yaml
```

Update `config/.env` with your email, calendar, timezone, and notion settings.

Then test the setup:

```bash
python scripts/test_simple.py
python scripts/debug.py --preview-only
```

Send a test email:

```bash
python main.py
```

## useful commands

```bash
python main.py
python run_tests.py
python scripts/debug.py --preview-only
python scripts/test_calendar.py
```

## security notes

- never commit `config/.env`
- use app passwords for email instead of your main password
- keep notion tokens private

## future improvements

- add google calendar api support
- improve recurring event handling
- add richer task grouping
- support multiple email templates
