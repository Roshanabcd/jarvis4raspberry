# API Specification — JARVIS Module 19 (`v1.0.0`)

Base URL: `/api/v1/computer-assistant`

- `GET /health`, `GET /manifest`, `GET /status`, `GET /diagnostics`
- `GET /apps`, `GET /windows`, `GET /screenshots`, `GET /screenshots/{screenshot_id}`
- `POST /safety/estop`, `POST /safety/estop/reset`, `PUT /safety/dry-run`, `PUT /safety/policy`
- `GET /actions`, `POST /actions`, `POST /actions/replay`
- `GET /approvals`, `POST /approvals/{approval_id}/decide`
- `GET /logs`, `WS /ws/events`
