# API Reference — JARVIS Module 32: System Health & Diagnostics (`v1.0.0`)

**Base URL:** `http://127.0.0.1:8132/api/v1/system-health`  
**WebSocket:** `ws://127.0.0.1:8132/api/v1/system-health/ws/metrics`

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Module health check (`simulated: false`) |
| `GET` | `/manifest` | Returns `manifest.json` |
| `GET` | `/status` | Hostname, load, memory/disk %, CPU temp, open alerts, service count |
| `GET` | `/metrics` | Full live local OS metrics snapshot |
| `POST` | `/snapshots/capture` | Capture & persist a host snapshot and evaluate alert rules |
| `GET` | `/snapshots` | List recent persisted snapshots |
| `GET` | `/rules` | List configured threshold alert rules |
| `POST` | `/rules` | Create a threshold alert rule |
| `GET` | `/alerts` | List alerts (optional `?unacknowledged_only=true`) |
| `POST` | `/alerts/{alert_id}/ack` | Acknowledge an alert |
| `GET` | `/services` | List registered localhost TCP service probes |
| `POST` | `/services` | Register a localhost service (`127.0.0.1`, `localhost`, `::1` only) |
| `POST` | `/services/probe` | Probe all registered services and record latency in ms |
| `POST` | `/diagnostics/run` | Run full scored diagnostic bundle (`0-100`) with recommendations |
| `GET` | `/diagnostics` | List historical diagnostic runs |
| `WS` | `/ws/metrics` | Real-time connection & heartbeat status stream |
