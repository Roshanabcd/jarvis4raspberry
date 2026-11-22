# API Reference — Module 26: Project Autopilot

Base prefix: `/api/v1/project-autopilot` (default standalone port: `8126`).

## Endpoints
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Module liveness, version, contract version, and `simulated` flag |
| `GET` | `/manifest` | Returns `manifest.json` metadata |
| `GET` | `/status` | Adapter name, `simulated` flag, project count, task progress, awaiting-approval count, uptime |
| `GET` | `/projects` | List all projects (newest first) |
| `POST` | `/projects` | Create a project and optionally auto-decompose into milestones/tasks |
| `GET` | `/projects/{project_id}` | Fetch project bundle (`project`, `progress_pct`, `milestones`, `tasks`, `logs`) |
| `POST` | `/projects/{project_id}/tasks` | Add a custom task with optional dependencies and approval gate |
| `POST` | `/projects/{project_id}/advance` | Run up to `max_steps` ready tasks respecting dependencies and approval gates |
| `POST` | `/projects/{project_id}/scaffold` | Scaffold starter files inside the sandboxed workspace root |
| `GET` | `/projects/{project_id}/blueprint.md` | Export project blueprint as `text/markdown` |
| `GET` | `/approvals` | List tasks currently paused in `awaiting_approval` |
| `POST` | `/tasks/{task_id}/approval` | Approve or reject a gated task (`decision`: `approve` \| `reject`) |
| `WS` | `/ws/events` | Real-time status stream (`ws.connected` + `ws.heartbeat`) |
