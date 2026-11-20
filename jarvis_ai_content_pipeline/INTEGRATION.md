# Integrating AI Content Creation Pipeline into JARVIS OS (Strictly Additive)

This package does **not** overwrite or modify existing `jarvis-os` files automatically.

## Step 1 — Extract Into Your JARVIS OS `features/` Directory

```bash
mkdir -p ~/.gemini/antigravity/scratch/jarvis-os/features
unzip jarvis_ai_content_pipeline.zip -d ~/.gemini/antigravity/scratch/jarvis-os/features/
```

## Step 2 — Mount the FastAPI Router in Your JARVIS Backend

Add 2 lines to your existing FastAPI backend entry point:

```python
from features.jarvis_ai_content_pipeline import create_router as create_content_pipeline_router

app.include_router(create_content_pipeline_router())
```

Endpoints exposed:
- **Web UI**: `GET /content-pipeline`
- **API**: `/api/content-pipeline/{health, blog, video-script, hooks-captions, carousel, campaign, history, item/{id}, item/{id}/export}`

## Step 3 — Enable the Dashboard Card

In your JARVIS OS dashboard registry, flip **AI Content Creation Pipeline** from `PLANNED` to `AVAILABLE` and link its **Open** button to `/content-pipeline` (or `http://127.0.0.1:8012/content-pipeline` if running standalone).
