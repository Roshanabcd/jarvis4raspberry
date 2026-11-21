# Module 37 — JARVIS OS Integration Guide

## Host Mounting
```python
from fastapi import FastAPI
from backend.app.config import DeviceMeshConfig
from backend.app.main import mount_module
from backend.services.device_mesh_engine import DeviceMeshEngine

app = FastAPI(title="JARVIS OS")
mount_module(app, engine=DeviceMeshEngine(DeviceMeshConfig.from_env()), include_root_ui=False)
```

- Exposes `app.state.devices` (`DeviceMeshEngine`).
- Mounts REST/WS routes under `/api/v1/devices/*` and the interactive HUD at `/devices`.
- Uses isolated SQLite WAL storage configured via `JARVIS_M37_DB_PATH`.
