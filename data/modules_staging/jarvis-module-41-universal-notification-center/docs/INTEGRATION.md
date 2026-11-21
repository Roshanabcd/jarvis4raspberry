# Module 41 — JARVIS OS Integration Guide

## Host Mounting
```python
from fastapi import FastAPI
from backend.app.config import NotificationConfig
from backend.app.main import mount_module
from backend.services.notification_engine import NotificationEngine

app = FastAPI(title="JARVIS OS")
mount_module(app, engine=NotificationEngine(NotificationConfig.from_env()), include_root_ui=False)
```

- Exposes `app.state.notifications` (`NotificationEngine`).
- Mounts REST/WS routes under `/api/v1/notifications/*` and the interactive HUD at `/notifications`.
- Uses isolated SQLite WAL storage configured via `JARVIS_M41_DB_PATH`.
