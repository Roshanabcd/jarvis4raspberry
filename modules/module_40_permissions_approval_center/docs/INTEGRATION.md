# Module 40 — JARVIS OS Integration Guide

## Host Mounting
```python
from fastapi import FastAPI
from backend.app.config import ApprovalConfig
from backend.app.main import mount_module
from backend.services.approval_engine import ApprovalEngine

app = FastAPI(title="JARVIS OS")
mount_module(app, engine=ApprovalEngine(ApprovalConfig.from_env()), include_root_ui=False)
```

- Exposes `app.state.approvals` (`ApprovalEngine`).
- Mounts REST/WS routes under `/api/v1/approvals/*` and the interactive HUD at `/approvals`.
- Uses isolated SQLite WAL storage configured via `JARVIS_M40_DB_PATH`.
