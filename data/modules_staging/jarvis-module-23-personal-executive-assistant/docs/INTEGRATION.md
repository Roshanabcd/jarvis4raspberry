# JARVIS OS Integration Guide — Module 23

Module 23 adheres to the **JARVIS Common Module Contract (`v1.0.0`)**.

## 1. Additive 2-Line FastAPI Mount
In `apps/core/main.py` (before any root `/` static catch-all):
```python
from backend.app.main import mount_module as mount_executive_assistant
mount_executive_assistant(app)
```

## 2. Database Isolation
- Stores all records in its isolated SQLite WAL database (`JARVIS_M23_DB_PATH`, default `./data/jarvis_executive_assistant.db`).
- Never modifies `jarvis_memory.db` or sibling module tables.

## 3. Connecting Live LLM Briefings (via Module 22)
Subclass `ExecutiveSynthesisAdapter` in `backend/adapters/executive_adapter.py` and forward the structured briefing context to Module 22's `/api/v1/model-router/route` endpoint with `strategy="local_only"` for private daily briefings.
