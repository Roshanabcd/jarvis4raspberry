# JARVIS OS Integration Guide — Module 43 (Autonomous Screen Guardian)

Module 43 is engineered to run **standalone** (`uvicorn backend.app.main:app --port 8143`) OR mount cleanly into an existing JARVIS OS FastAPI host application (such as `/home/roshan/.gemini/antigravity/scratch/jarvis-os`) without modifying JARVIS core files.

## 1. Mounting into a Host JARVIS FastAPI App

```python
from fastapi import FastAPI
from backend.app.config import ScreenGuardianConfig
from backend.app.main import mount_module
from backend.services.guardian_service import ScreenGuardianService

jarvis_app = FastAPI(title="JARVIS OS Core")

config = ScreenGuardianConfig.from_env()
guardian_service = ScreenGuardianService(config=config)

# Mounts all /api/v1/screen-guardian/* REST & WS routes and /screen-guardian HUD
# include_root_ui=False ensures JARVIS Core's "/" dashboard route is never overwritten
mount_module(jarvis_app, guardian_service, include_root_ui=False)
```

## 2. Manifest & Module 42 Compatibility

`manifest.json` follows the JARVIS OS Unified Extension Manager (Module 42) schema:
- `module_id`: `jarvis-module-43-autonomous-screen-guardian`
- `api_prefix`: `/api/v1/screen-guardian`
- `ws_endpoint`: `/api/v1/screen-guardian/ws/stream`
- `standalone_hud`: `/screen-guardian`
- `default_port`: `8143`

## 3. Frontend Integration

You can embed Module 43 in the JARVIS OS dashboard in two ways:
1. **Zero-Build Standalone HUD**: Link or iframe `/screen-guardian` directly from the JARVIS launchpad.
2. **React/TypeScript Module**: Import `frontend/src/pages/DashboardPage.tsx` and `frontend/src/services/api.ts` into the JARVIS React frontend, configuring `VITE_API_BASE` if proxying to port `8143`.

## 4. Event & Voice Integration Hooks

- **WebSocket Events**: Subscribe to `/api/v1/screen-guardian/ws/stream` to feed live `error.detected` events into Module 41 (Universal Notification Center) or JARVIS Core alerts.
- **Voice Pipeline**: Forward microphone-transcribed utterances from Module 20 (Real-Time Conversational AI) to `POST /api/v1/screen-guardian/voice/command` with `speaker_source="user_mic"`.
- **Approval Governance**: Forward repair approval requests to Module 40 (Permissions & Approval Center) and post decisions back to `POST /api/v1/screen-guardian/repairs/{repair_id}/approve`.
