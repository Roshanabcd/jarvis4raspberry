# Integration Guide — JARVIS OS Module 25

## Standalone Mode
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8125
```
- UI: `http://127.0.0.1:8125/meeting-assistant`
- Health: `http://127.0.0.1:8125/api/v1/meeting-assistant/health`

## Mounting Into Existing JARVIS OS FastAPI App
```python
from backend.app.main import mount_module

mount_module(app, include_root_ui=False)
```
- Registers all REST & WebSocket endpoints under `/api/v1/meeting-assistant/*`.
- Registers the UI at `/meeting-assistant` without conflicting with JARVIS OS's root `/` dashboard.
- Stores all data in an isolated SQLite WAL database configured via `JARVIS_M25_DB_PATH` (default `./data/jarvis_meeting_assistant.db`), never touching `jarvis_memory.db`.

## Custom LLM / Transcription Adapter
Implement `MeetingSynthesisAdapter` in `backend/adapters/meeting_adapter.py`, set `is_simulated = False`, and pass your adapter into `MeetingAssistantEngine(adapter=YourAdapter())` before calling `mount_module(app, engine=engine)`.
