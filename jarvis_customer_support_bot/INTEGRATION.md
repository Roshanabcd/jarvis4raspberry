# Integrating Customer Support Bot into JARVIS OS (Strictly Additive)

This package does **not** overwrite or modify existing `jarvis-os` files automatically.

## Step 1 — Extract Into Your JARVIS OS `features/` Directory

```bash
mkdir -p ~/.gemini/antigravity/scratch/jarvis-os/features
unzip jarvis_customer_support_bot.zip -d ~/.gemini/antigravity/scratch/jarvis-os/features/
```

## Step 2 — Mount the FastAPI Router in Your JARVIS Backend

Add 2 lines to your existing FastAPI backend entry point:

```python
from features.jarvis_customer_support_bot import create_router as create_support_bot_router

app.include_router(create_support_bot_router())
```

Endpoints exposed:
- **Web UI**: `GET /support-bot`
- **API**: `/api/support-bot/{health, kb, inquire, tickets, tickets/{id}, stats}`

## Step 3 — Enable the Dashboard Card

In your JARVIS OS dashboard registry, flip **ChatGPT-Powered Customer Support Bot** from `PLANNED` to `AVAILABLE` and link its **Open** button to `/support-bot` (or `http://127.0.0.1:8018/support-bot` if running standalone).
