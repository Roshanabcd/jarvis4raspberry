# Module 40 — API Reference (`/api/v1/approvals`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/approvals/health` | Module health & contract metadata (`simulated: false`) |
| `GET` | `/api/v1/approvals/manifest` | Returns `manifest.json` |
| `GET` | `/api/v1/approvals/status` | Policy, request, pending queue, and audit counts |
| `GET` | `/api/v1/approvals/policies` | List configured governance policies |
| `POST` | `/api/v1/approvals/policies` | Upsert a `(module_id, action)` policy rule |
| `GET` | `/api/v1/approvals/requests` | List approval requests (optional `?status=pending`) |
| `POST` | `/api/v1/approvals/requests` | Submit an action request for policy evaluation / human review |
| `POST` | `/api/v1/approvals/requests/{request_id}/decide` | Approve or deny a pending request (`409` decided, `410` expired) |
| `GET` | `/api/v1/approvals/audit` | List immutable governance audit events |
| `WS` | `/api/v1/approvals/ws/requests` | Live approval queue & heartbeat WebSocket stream |
