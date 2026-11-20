# Integrating AI Interview Bot into JARVIS OS (Strictly Additive)

This package does **not** overwrite or modify existing `jarvis-os` files automatically.

## Step 1 — Extract Into Your JARVIS OS `features/` Directory

```bash
mkdir -p ~/.gemini/antigravity/scratch/jarvis-os/features
unzip jarvis_ai_interview_bot.zip -d ~/.gemini/antigravity/scratch/jarvis-os/features/
```

## Step 2 — Mount the FastAPI Router in Your JARVIS Backend

Add 2 lines to your existing FastAPI backend entry point:

```python
from features.jarvis_ai_interview_bot import create_router as create_interview_bot_router

app.include_router(create_interview_bot_router())
```

Endpoints exposed:
- **Web UI**: `GET /interview-bot`
- **API**: `/api/interview-bot/{health, sessions, sessions/start, sessions/{id}/answer, sessions/{id}/report, sessions/{id}/export}`

## Step 3 — Enable the Dashboard Card

In your JARVIS OS dashboard registry, flip **AI Interview Bot** from `PLANNED` to `AVAILABLE` and link its **Open** button to `/interview-bot` (or `http://127.0.0.1:8013/interview-bot` if running standalone).
