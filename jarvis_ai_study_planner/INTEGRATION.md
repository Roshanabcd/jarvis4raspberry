# Integrating AI Study Planner into JARVIS OS (Strictly Additive)

This package does **not** overwrite or modify existing `jarvis-os` files automatically.

## Step 1 — Extract Into Your JARVIS OS `features/` Directory

```bash
mkdir -p ~/.gemini/antigravity/scratch/jarvis-os/features
unzip jarvis_ai_study_planner.zip -d ~/.gemini/antigravity/scratch/jarvis-os/features/
```

## Step 2 — Mount the FastAPI Router in Your JARVIS Backend

Add 2 lines to your existing FastAPI backend entry point:

```python
from features.jarvis_ai_study_planner import create_router as create_study_planner_router

app.include_router(create_study_planner_router())
```

Endpoints exposed:
- **Web UI**: `GET /study-planner`
- **API**: `/api/study-planner/{health, plans, plans/{id}, plans/{id}/export, milestones/{id}, flashcards, flashcards/{id}/review, progress}`

## Step 3 — Enable the Dashboard Card

In your JARVIS OS dashboard registry, flip **AI Study Planner** from `PLANNED` to `AVAILABLE` and link its **Open** button to `/study-planner` (or `http://127.0.0.1:8015/study-planner` if running standalone).
