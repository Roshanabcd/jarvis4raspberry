# Integration Guide — JARVIS OS Module 29

## Standalone Mode
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8129
```
- UI: `http://127.0.0.1:8129/file-manager`
- Health: `http://127.0.0.1:8129/api/v1/file-manager/health`

## Mounting Into Existing JARVIS OS FastAPI App
```python
from backend.app.main import mount_module

mount_module(app, include_root_ui=False)
```
- Registers all REST & WebSocket endpoints under `/api/v1/file-manager/*` and UI at `/file-manager`.
- Confines all filesystem actions to `JARVIS_M29_ROOT_DIR` (default `./data/managed_files`) and stores tags/trash/audit logs in `JARVIS_M29_DB_PATH` (`./data/jarvis_file_manager.db`).
