# API Reference — Module 24: Email & Calendar Assistant

Base prefix: `/api/v1/email-calendar`  
UI route: `/email-calendar`  
Contract version: `1.0.0`

## Endpoints
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/email-calendar/health` | Module health, version, contract version, and simulation flag |
| `GET` | `/api/v1/email-calendar/manifest` | Returns `manifest.json` |
| `GET` | `/api/v1/email-calendar/status` | Inbox, unread, urgent, draft, pending approval, and calendar event counts |
| `GET` / `POST` | `/api/v1/email-calendar/emails` | List triaged emails or ingest a new email |
| `POST` | `/api/v1/email-calendar/emails/{email_id}/draft-reply` | Generate a reply draft for an email |
| `POST` | `/api/v1/email-calendar/emails/{email_id}/archive` | Mark email read and archive |
| `GET` / `POST` | `/api/v1/email-calendar/drafts` | List or compose email drafts |
| `POST` | `/api/v1/email-calendar/drafts/{draft_id}/send` | Queue draft for human send approval (or dispatch if gate disabled) |
| `GET` | `/api/v1/email-calendar/approvals` | List outbound send approval requests |
| `POST` | `/api/v1/email-calendar/approvals/{approval_id}/decide` | Approve (dispatch) or reject a pending outbound email |
| `GET` / `POST` | `/api/v1/email-calendar/calendar/events` | List or schedule overlap-checked calendar events (`409` on conflict) |
| `PATCH` | `/api/v1/email-calendar/calendar/events/{event_id}/rsvp` | Update event RSVP (`accepted`, `tentative`, `declined`, `cancelled`) |
| `POST` | `/api/v1/email-calendar/calendar/find-slots` | Find conflict-free workday slots of at least `duration_minutes` |
| `GET` | `/api/v1/email-calendar/calendar/export.ics` | Export scheduled events in RFC 5545 iCalendar (`.ics`) format |
| `WS` | `/api/v1/email-calendar/ws/events` | Real-time status & heartbeat WebSocket stream |
