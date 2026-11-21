# Integration Guide — JARVIS OS Module 28

## Standalone Mode
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8128
```
- UI: `http://127.0.0.1:8128/ai-data-analyst`
- Health: `http://127.0.0.1:8128/api/v1/ai-data-analyst/health`

## Mounting Into Existing JARVIS OS FastAPI App
```python
from backend.app.main import mount_module

mount_module(app, include_root_ui=False)
```
- Registers all REST & WebSocket endpoints under `/api/v1/ai-data-analyst/*` and UI at `/ai-data-analyst`.
- Uses an isolated SQLite WAL database (`JARVIS_M28_DB_PATH`, default `./data/jarvis_ai_data_analyst.db`).

## Connecting an External LLM Narrative Adapter
Implement `DataInsightAdapter` in `backend/adapters/insight_adapter.py`, set `is_simulated = False`, and inject it into `DataAnalystEngine(adapter=YourAdapter())`.
