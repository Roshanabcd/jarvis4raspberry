# Module 37 — API Reference (`/api/v1/devices`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/devices/health` | Module health & contract metadata (`simulated: true`) |
| `GET` | `/api/v1/devices/manifest` | Returns `manifest.json` |
| `GET` | `/api/v1/devices/status` | Mesh node, online, command, and clipboard counts |
| `GET` | `/api/v1/devices/nodes` | List registered mesh devices |
| `POST` | `/api/v1/devices/nodes` | Register a new mesh device with capabilities |
| `POST` | `/api/v1/devices/nodes/{device_id}/heartbeat` | Update device online state & battery percentage |
| `POST` | `/api/v1/devices/nodes/{device_id}/commands` | Dispatch capability-guarded command (`409` offline / `422` unsupported) |
| `GET` | `/api/v1/devices/commands` | List command audit history (optional `?device_id=`) |
| `GET` | `/api/v1/devices/clipboard` | List shared clipboard history |
| `POST` | `/api/v1/devices/clipboard` | Push a new SHA-256-hashed clipboard entry |
| `WS` | `/api/v1/devices/ws/mesh` | Live mesh status & heartbeat WebSocket stream |
