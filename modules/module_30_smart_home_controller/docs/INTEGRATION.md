# JARVIS OS Integration Guide — Module 30 (Smart Home Controller)

## 1. Mounting Inside JARVIS OS Core
Module 30 exposes `mount_module(app, engine=None, include_root_ui=False)` in `backend/app/main.py` so it can be embedded directly into the main JARVIS OS FastAPI server (`/home/roshan/.gemini/antigravity/scratch/jarvis-os`) without port conflicts:

```python
from fastapi import FastAPI
from backend.app.config import SmartHomeConfig
from backend.app.main import mount_module
from backend.services.smart_home_engine import SmartHomeEngine

jarvis_app = FastAPI(title="JARVIS OS Core")
m30_engine = SmartHomeEngine(SmartHomeConfig(db_path="./data/jarvis_smart_home.db"))
mount_module(jarvis_app, engine=m30_engine, include_root_ui=False)
```

Once mounted:
- **REST API**: `/api/v1/smart-home/*`
- **WebSocket**: `/api/v1/smart-home/ws/events`
- **Control UI**: `/smart-home`
- **App State Handle**: `jarvis_app.state.smart_home`

## 2. Standalone Microservice Mode
Run on port `8130` via `bash scripts/run.sh` and register `http://127.0.0.1:8130/api/v1/smart-home/manifest` in the JARVIS OS module registry.

## 3. Connecting Real Hardware Bridges
Subclass `SmartHomeBridgeAdapter` in `backend/adapters/bridge_adapter.py`:
- Set `adapter_name` (e.g., `"home_assistant_rest"` or `"mqtt_zigbee2mqtt"`).
- Set `is_simulated = False`.
- Implement `dispatch(device, command, value)` to translate JARVIS commands into MQTT topics, Home Assistant service calls, or Matter commands.
- Pass your adapter instance into `SmartHomeEngine(config, bridge=MyHardwareBridge())`.

## 4. Environment Variables
| Variable | Default | Description |
| --- | --- | --- |
| `JARVIS_M30_HOST` | `0.0.0.0` | Bind host for standalone Uvicorn server |
| `JARVIS_M30_PORT` | `8130` | Bind port for standalone Uvicorn server |
| `JARVIS_M30_DB_PATH` | `./data/jarvis_smart_home.db` | SQLite WAL database path |
| `JARVIS_M30_CORS_ORIGINS` | `*` | Comma-separated CORS origins |
