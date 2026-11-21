# API Reference — JARVIS Module 33: Defensive Cybersecurity Agent (`v1.0.0`)

**Base URL:** `http://127.0.0.1:8133/api/v1/cybersecurity`  
**WebSocket:** `ws://127.0.0.1:8133/api/v1/cybersecurity/ws/alerts`

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Module health check (`simulated: false`) |
| `GET` | `/manifest` | Returns `manifest.json` |
| `GET` | `/status` | Security posture score (`0-100`), open incidents, baselines & scans count |
| `POST` | `/scan/secrets` | Scan a sandboxed relative path for leaked secrets & world-writable files |
| `GET` | `/scans` | List recent secret scan runs |
| `POST` | `/fim/baseline` | Compute and persist a SHA-256 File Integrity Monitoring baseline |
| `GET` | `/fim/baselines` | List all FIM baselines |
| `POST` | `/fim/verify/{baseline_id}` | Detect `modified`, `added`, and `deleted` files against a baseline |
| `POST` | `/logs/analyze` | Analyze auth/syslog/HTTP log lines for brute-force & payload anomalies |
| `GET` | `/incidents` | List incidents (optional `?status=open` or `?status=resolved`) |
| `POST` | `/incidents/{incident_id}/resolve` | Mark an incident resolved with a resolution note |
| `WS` | `/ws/alerts` | Real-time connection & heartbeat posture stream |
