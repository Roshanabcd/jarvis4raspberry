# Module 39 — API Reference (`/api/v1/backups`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/backups/health` | Module health & contract metadata (`simulated: false`) |
| `GET` | `/api/v1/backups/manifest` | Returns `manifest.json` |
| `GET` | `/api/v1/backups/status` | Snapshot count, restore count, total archive bytes, uptime |
| `GET` | `/api/v1/backups/snapshots` | List persisted backup snapshots |
| `POST` | `/api/v1/backups/snapshots` | Create a real ZIP snapshot from a sandboxed relative path |
| `POST` | `/api/v1/backups/snapshots/{snapshot_id}/verify` | Verify SHA-256 digest and ZIP CRC integrity |
| `POST` | `/api/v1/backups/snapshots/{snapshot_id}/restore` | Verify integrity and restore files into a sandboxed target directory |
| `GET` | `/api/v1/backups/restores` | List restore history (optional `?snapshot_id=`) |
| `WS` | `/api/v1/backups/ws/snapshots` | Live backup status & heartbeat WebSocket stream |
