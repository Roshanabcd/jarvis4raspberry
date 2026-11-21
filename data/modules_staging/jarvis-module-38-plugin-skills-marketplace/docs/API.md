# Module 38 — API Reference (`/api/v1/marketplace`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/marketplace/health` | Module health & contract metadata (`simulated: false`) |
| `GET` | `/api/v1/marketplace/manifest` | Returns `manifest.json` |
| `GET` | `/api/v1/marketplace/status` | Package, installed, enabled, and audit counts |
| `GET` | `/api/v1/marketplace/packages` | List or search (`?q=`) catalog packages |
| `POST` | `/api/v1/marketplace/packages` | Publish a new SemVer plugin/skill (`422` invalid, `409` duplicate) |
| `POST` | `/api/v1/marketplace/packages/{package_id}/install` | Install package with optional `expected_sha256` verification |
| `POST` | `/api/v1/marketplace/packages/{package_id}/toggle` | Enable or disable an installed package |
| `DELETE` | `/api/v1/marketplace/packages/{package_id}/install` | Uninstall an installed package |
| `GET` | `/api/v1/marketplace/audit` | List marketplace audit log events |
| `WS` | `/api/v1/marketplace/ws/registry` | Live registry status & heartbeat WebSocket stream |
