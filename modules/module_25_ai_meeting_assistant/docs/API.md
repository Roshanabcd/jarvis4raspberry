# API Reference — Module 25: AI Meeting Assistant

Base prefix: `/api/v1/meeting-assistant` (default standalone port: `8125`).

## Endpoints
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Module liveness, version, contract version, and `simulated` flag |
| `GET` | `/manifest` | Returns `manifest.json` metadata |
| `GET` | `/status` | Adapter name, `simulated` status, meeting count, open/completed action counts, uptime |
| `GET` | `/meetings` | List all meetings (newest first) |
| `POST` | `/meetings` | Create a meeting (`title`, `meeting_date`, `participants`, `agenda`) |
| `GET` | `/meetings/{meeting_id}` | Fetch meeting details, transcript `segments`, and `action_items` |
| `POST` | `/meetings/{meeting_id}/transcript` | Append a single segment (`speaker`, `text`, `timestamp_sec`) |
| `POST` | `/meetings/{meeting_id}/transcript/bulk` | Bulk-ingest `Speaker: text` lines (`raw_transcript`) |
| `POST` | `/meetings/{meeting_id}/analyze` | Compute speaker talk-share, extract decisions/risks/action items, and synthesize overview |
| `GET` | `/meetings/{meeting_id}/minutes.md` | Export meeting minutes as `text/markdown` |
| `GET` | `/action-items?status=open\|done` | List action items across meetings, optionally filtered by status |
| `PATCH` | `/action-items/{item_id}` | Update action item status (`open` or `done`) |
| `GET` | `/search?q=...` | Full-text search across all transcript segments |
| `WS` | `/ws/events` | Real-time status stream (`ws.connected` + `ws.heartbeat`) |
