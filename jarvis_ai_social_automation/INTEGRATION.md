# Integrating AI Social Media Automation into JARVIS OS (Strictly Additive)

This package does **not** overwrite or modify existing `jarvis-os` files automatically.

## Step 1 — Extract Into Your JARVIS OS `features/` Directory

```bash
mkdir -p ~/.gemini/antigravity/scratch/jarvis-os/features
unzip jarvis_ai_social_automation.zip -d ~/.gemini/antigravity/scratch/jarvis-os/features/
```

## Step 2 — Mount the FastAPI Router in Your JARVIS Backend

Add 2 lines to your existing FastAPI backend entry point:

```python
from features.jarvis_ai_social_automation import create_router as create_social_automation_router

app.include_router(create_social_automation_router())
```

Endpoints exposed:
- **Web UI**: `GET /social-automation`
- **API**: `/api/social-automation/{health, plan, posts, posts/{id}/publish, posts/{id}/metrics, scheduler/run-due, analytics}`

## Step 3 — Enable the Dashboard Card

In your JARVIS OS dashboard registry, flip **AI Social Media Automation** from `PLANNED` to `AVAILABLE` and link its **Open** button to `/social-automation` (or `http://127.0.0.1:8014/social-automation` if running standalone).
