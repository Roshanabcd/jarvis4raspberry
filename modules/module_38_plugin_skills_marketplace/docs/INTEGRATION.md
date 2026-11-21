# Module 38 — JARVIS OS Integration Guide

## Host Mounting
```python
from fastapi import FastAPI
from backend.app.config import MarketplaceConfig
from backend.app.main import mount_module
from backend.services.marketplace_engine import MarketplaceEngine

app = FastAPI(title="JARVIS OS")
mount_module(app, engine=MarketplaceEngine(MarketplaceConfig.from_env()), include_root_ui=False)
```

- Exposes `app.state.marketplace` (`MarketplaceEngine`).
- Mounts REST/WS routes under `/api/v1/marketplace/*` and the interactive HUD at `/marketplace`.
- Uses isolated SQLite WAL storage configured via `JARVIS_M38_DB_PATH`.
