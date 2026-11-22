# Module 41 — API Reference (`/api/v1/notifications`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/notifications/health` | Module health & contract metadata (`simulated: false`) |
| `GET` | `/api/v1/notifications/manifest` | Returns `manifest.json` |
| `GET` | `/api/v1/notifications/status` | Total, unread, suppressed counts and DND status |
| `GET` | `/api/v1/notifications/preferences` | Fetch DND & enabled channel preferences |
| `PUT` | `/api/v1/notifications/preferences` | Update DND, critical override, and enabled channels |
| `GET` | `/api/v1/notifications/items` | List notifications (optional `?status=` / `?priority=`) |
| `POST` | `/api/v1/notifications/items` | Dispatch notification with DND routing & deduplication |
| `POST` | `/api/v1/notifications/items/{notification_id}/ack` | Acknowledge an alert |
| `POST` | `/api/v1/notifications/items/{notification_id}/dismiss` | Dismiss an alert |
| `WS` | `/api/v1/notifications/ws/stream` | Live notification status & heartbeat WebSocket stream |
