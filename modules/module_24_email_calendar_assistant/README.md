# JARVIS OS — Module 24: Email & Calendar Assistant (`v1.0.0`)

Policy-governed Email & Calendar module for **JARVIS OS**, providing smart inbox triage, reply draft composition with mandatory human approval gates before outbound sending, overlap-checked calendar scheduling, a workday free-slot finder, RFC 5545 iCalendar (`.ics`) export, SQLite WAL persistence, and a futuristic JARVIS-themed control UI.

> **Simulation Transparency**: By default, Module 24 runs with `SimulatedMailCalendarAdapter` (`simulated: true`) so no real SMTP/Gmail messages are transmitted or external calendars altered. Subclass `MailCalendarAdapter` to wire live Gmail API / IMAP / SMTP / Google Calendar credentials when explicitly authorized.

## Quick Start
```bash
bash scripts/setup.sh
bash scripts/run.sh
# Open http://127.0.0.1:8124/email-calendar
```

## Run Automated Tests & Demo
```bash
bash scripts/test.sh
python3 examples/run_email_calendar_demo.py
```

## Documentation
- [API Reference](docs/API.md)
- [JARVIS OS Integration Guide](docs/INTEGRATION.md)
- [Security & Outbound Approval Policy](docs/SECURITY.md)
- [Test Verification Report](docs/TEST_REPORT.md)
