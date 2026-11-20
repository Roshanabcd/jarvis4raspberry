# Integrating Autonomous Web Scraping Agent into JARVIS OS (Strictly Additive)

This package does **not** overwrite or modify existing `jarvis-os` files automatically.

## Step 1 — Extract Into Your JARVIS OS `features/` Directory

```bash
mkdir -p ~/.gemini/antigravity/scratch/jarvis-os/features
unzip jarvis_web_scraping_agent.zip -d ~/.gemini/antigravity/scratch/jarvis-os/features/
```

## Step 2 — Mount the FastAPI Router in Your JARVIS Backend

Add 2 lines to your existing FastAPI backend entry point:

```python
from features.jarvis_web_scraping_agent import create_router as create_web_scraper_router

app.include_router(create_web_scraper_router())
```

Endpoints exposed:
- **Web UI**: `GET /web-scraper`
- **API**: `/api/web-scraper/{health, extract, monitors, monitors/{id}/check, snapshots, snapshots/{id}/export}`

## Step 3 — Enable the Dashboard Card

In your JARVIS OS dashboard registry, flip **Autonomous Web Scraping Agent** from `PLANNED` to `AVAILABLE` and link its **Open** button to `/web-scraper` (or `http://127.0.0.1:8017/web-scraper` if running standalone).
