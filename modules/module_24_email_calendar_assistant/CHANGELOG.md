# Changelog

## [1.0.0] — Initial Release
### Added
- `EmailCalendarDB` SQLite WAL persistence (`emails`, `email_drafts`, `send_approvals`, `calendar_events`).
- `MailCalendarAdapter` contract and offline `SimulatedMailCalendarAdapter`.
- `EmailCalendarEngine` with deterministic email triage, reply draft composition, human-approval outbound send gates, overlap-checked calendar scheduling, workday free-slot finder, and RFC 5545 `.ics` export.
- FastAPI REST (`/api/v1/email-calendar/*`), WebSocket (`/api/v1/email-calendar/ws/events`), and `mount_module(app)` integration hook.
- Standalone JARVIS-themed Control UI (`backend/app/static/index.html`) and React/TypeScript/Vite/Tailwind frontend (`frontend/`).
- Automated backend, API, integration, frontend, and E2E test suites plus runnable CLI demo.
