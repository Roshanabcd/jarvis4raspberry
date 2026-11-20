# Integrating Autonomous Trading Bot into JARVIS OS (Strictly Additive)

This package is hard-locked to **simulated paper trading** and does **not** overwrite or modify existing `jarvis-os` files automatically.

## Step 1 — Extract Into Your JARVIS OS `features/` Directory

```bash
mkdir -p ~/.gemini/antigravity/scratch/jarvis-os/features
unzip jarvis_autonomous_trading_bot.zip -d ~/.gemini/antigravity/scratch/jarvis-os/features/
```

## Step 2 — Mount the FastAPI Router in Your JARVIS Backend

Add 2 lines to your existing FastAPI backend entry point:

```python
from features.jarvis_autonomous_trading_bot import create_router as create_trading_bot_router

app.include_router(create_trading_bot_router())
```

Endpoints exposed:
- **Web UI**: `GET /trading-bot`
- **API**: `/api/trading-bot/{health, portfolio, estop, analyze, backtest, orders}`

## Step 3 — Enable the Dashboard Card

In your JARVIS OS dashboard registry, flip **Autonomous Trading Bot** from `PLANNED` to `AVAILABLE` and link its **Open** button to `/trading-bot` (or `http://127.0.0.1:8016/trading-bot` if running standalone).
