# API Reference — JARVIS Module 42 (`v1.0.0`)

Base URL: `/api/v1/extensions` (Default standalone port: `8142`). OpenAPI docs at `/docs`.

## System
- `GET /health` — Health, contract version (`1.0.0`), SDK version (`1.0.0`), `simulated: false`.
- `GET /manifest` — Returns `manifest.json`.
- `GET /status` — Module totals, enabled count, health breakdown, conflict count, pending approvals.

## Scanner & Compatibility
- `POST /scan` *(Auth)* — Body `{folder_path, register_discovered, target_arch}`. Safely inspects all `.zip` files in-memory without executing packaged code.
- `GET /compatibility/conflicts` — Cross-module port, API prefix, and Python dependency pin conflicts.

## Persistent Module Registry & Health
- `GET /modules?enabled=true|false` — List registered modules.
- `POST /modules` *(Auth)* — Register or update a module record.
- `GET /modules/{module_id}` — Detailed module metadata, compatibility report, permissions, and config.
- `POST /modules/{module_id}/toggle` *(Auth)* — Body `{enabled: true|false}`.
- `PUT /modules/{module_id}/config` *(Auth)* — Update module config, `health_endpoint`, or `installed_location`.
- `POST /modules/{module_id}/health-check` *(Auth)* — Real async HTTP health probe (`healthy`, `degraded`, `unavailable`, `not_configured`, `not_verified`, `disabled`).

## Dry-Run Install Planner & Approvals
- `POST /plan` — Body `{module_ids, target_arch}`. Returns topological install order, conflicts, permissions, required config, and rollback instructions (`dry_run: true`, `auto_execute: false`).
- `GET /approvals` | `POST /approvals` *(Auth)* | `POST /approvals/{request_id}/decide` *(Auth)*

## Shared Event Bus & Audit Logs
- `POST /events/publish` *(Auth)* | `GET /events` | `GET /logs` | `WS /ws/events`
