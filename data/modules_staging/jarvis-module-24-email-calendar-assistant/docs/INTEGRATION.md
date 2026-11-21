# JARVIS OS Integration Guide — Module 24

Module 24 follows the **JARVIS Common Module Contract (`v1.0.0`)**.

## 1. Additive 2-Line FastAPI Mount
In `apps/core/main.py` (before any root `/` static catch-all):
```python
from backend.app.main import mount_module as mount_email_calendar
mount_email_calendar(app)
```

## 2. Database Isolation
- Isolated SQLite WAL database at `JARVIS_M24_DB_PATH` (default `./data/jarvis_email_calendar.db`).
- Never modifies `jarvis_memory.db` or sibling modules.

## 3. Wiring Live Mail & Calendar Providers
Subclass `MailCalendarAdapter` in `backend/adapters/mail_calendar_adapter.py` to integrate Gmail API / SMTP / CalDAV / Google Calendar, set `is_simulated = False`, and inject it into `EmailCalendarEngine(config, adapter=YourLiveAdapter())`. Outbound human approval gates remain enforced by default.
