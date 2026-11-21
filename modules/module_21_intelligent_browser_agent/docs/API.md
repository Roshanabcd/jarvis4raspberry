# API Reference — Module 21: Intelligent Browser Agent

Base prefix: `/api/v1/browser-agent`  
UI route: `/browser-agent`  
Contract version: `1.0.0`

## System & Policy Endpoints
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/browser-agent/health` | Module health, version, contract version, and simulation status |
| `GET` | `/api/v1/browser-agent/manifest` | Returns `manifest.json` |
| `GET` | `/api/v1/browser-agent/status` | Live counts (sessions, workflows, pending approvals, downloads) and active site policy |
| `PUT` | `/api/v1/browser-agent/policy` | Update `allowed_domains`, `blocked_domains`, `require_approval_for_form_submit`, `allow_downloads` |

## Session, Navigation, DOM, Form & Download Endpoints
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/browser-agent/sessions` | List browser sessions |
| `POST` | `/api/v1/browser-agent/sessions` | Create a new session (`name`, `start_url`) and load initial DOM |
| `POST` | `/api/v1/browser-agent/sessions/{session_id}/close` | Close an active session |
| `POST` | `/api/v1/browser-agent/sessions/{session_id}/navigate` | Navigate to a policy-approved URL (`{"url": "..."}`) |
| `GET` | `/api/v1/browser-agent/sessions/{session_id}/inspect` | Extract real HTML DOM of the current page |
| `POST` | `/api/v1/browser-agent/sessions/{session_id}/screenshot` | Capture and analyze a Pillow PNG screenshot (returns base64 PNG + metrics) |
| `POST` | `/api/v1/browser-agent/sessions/{session_id}/form/fill` | Stage form field values (`form_id`, `fields`) without submitting |
| `POST` | `/api/v1/browser-agent/sessions/{session_id}/form/submit` | Request form submission; queues human approval when policy requires it |
| `POST` | `/api/v1/browser-agent/sessions/{session_id}/download` | Download a file into the sandboxed downloads directory with SHA-256 verification |

## Workflows, Approvals, Downloads, Logs & WebSocket
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/browser-agent/workflows` | List multi-page workflows |
| `POST` | `/api/v1/browser-agent/workflows` | Execute a multi-page workflow (`name`, `session_id`, `steps`) |
| `POST` | `/api/v1/browser-agent/workflows/{task_id}/cancel` | Cancel an active or paused workflow |
| `GET` | `/api/v1/browser-agent/approvals` | List form submission approval requests (optional `?status=pending`) |
| `POST` | `/api/v1/browser-agent/approvals/{approval_id}/decide` | Approve or reject a pending submission (`approved`, `decided_by`, `comment`); approving automatically executes submission and resumes paused workflows |
| `GET` | `/api/v1/browser-agent/downloads` | List sandboxed downloads and SHA-256 hashes |
| `GET` | `/api/v1/browser-agent/logs` | Retrieve browser automation audit logs (`?limit=120`) |
| `WS` | `/api/v1/browser-agent/ws/events` | Real-time status & heartbeat WebSocket stream |
