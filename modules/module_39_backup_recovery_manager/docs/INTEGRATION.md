# Module 39 — JARVIS OS Integration Guide

## Host Mounting
```python
from fastapi import FastAPI
from backend.app.config import BackupConfig
from backend.app.main import mount_module
from backend.services.backup_engine import BackupEngine

app = FastAPI(title="JARVIS OS")
mount_module(app, engine=BackupEngine(BackupConfig.from_env()), include_root_ui=False)
```

- Exposes `app.state.backups` (`BackupEngine`).
- Mounts REST/WS routes under `/api/v1/backups/*` and the interactive HUD at `/backups`.
- Configure `JARVIS_M39_SANDBOX_ROOT`, `JARVIS_M39_ARCHIVE_DIR`, and `JARVIS_M39_DB_PATH` in `.env`.
