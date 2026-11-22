# Integration Guide — JARVIS OS Module 26

## Standalone Mode
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8126
```
- UI: `http://127.0.0.1:8126/project-autopilot`
- Health: `http://127.0.0.1:8126/api/v1/project-autopilot/health`

## Mounting Into Existing JARVIS OS FastAPI App
```python
from backend.app.main import mount_module

mount_module(app, include_root_ui=False)
```
- Registers all REST & WebSocket endpoints under `/api/v1/project-autopilot/*`.
- Registers the UI at `/project-autopilot` without colliding with JARVIS OS's root `/` route.
- Stores all state in an isolated SQLite WAL database (`JARVIS_M26_DB_PATH`, default `./data/jarvis_project_autopilot.db`) and scaffolds files strictly inside `JARVIS_M26_WORKSPACE_ROOT` (`./data/workspaces`).

## Pluggable Planner / Codegen Adapter
Implement `ProjectPlannerAdapter` in `backend/adapters/planner_adapter.py`, set `is_simulated = False`, and inject it into `ProjectAutopilotEngine(adapter=YourAdapter())` before calling `mount_module(app, engine=engine)`.
