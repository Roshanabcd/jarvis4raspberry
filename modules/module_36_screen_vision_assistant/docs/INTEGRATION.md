# Module 36 — JARVIS OS Integration Guide

## Host Mounting
```python
from fastapi import FastAPI
from backend.app.config import VisionConfig
from backend.app.main import mount_module
from backend.services.vision_engine import VisionEngine

app = FastAPI(title="JARVIS OS")
mount_module(app, engine=VisionEngine(VisionConfig.from_env()), include_root_ui=False)
```

- Exposes `app.state.vision` (`VisionEngine`).
- Mounts REST/WS routes under `/api/v1/vision/*` and the interactive HUD at `/vision`.
- Uses isolated SQLite WAL storage configured via `JARVIS_M36_DB_PATH`.
