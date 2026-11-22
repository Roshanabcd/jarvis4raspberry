"""Standalone FastAPI entry point for Autonomous Trading Bot (Paper Trading Only)."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .config import TradingBotConfig
from .router import create_router


def create_app(config: Optional[TradingBotConfig] = None) -> FastAPI:
    app = FastAPI(
        title="JARVIS OS — Autonomous Trading Bot (Paper Only)",
        version="1.0.0",
        description="Simulated paper trading, technical analysis, backtesting engine, and risk-managed execution models.",
    )
    app.include_router(create_router(config=config))

    @app.get("/", include_in_schema=False)
    async def root_redirect() -> RedirectResponse:
        return RedirectResponse(url="/trading-bot")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("JARVIS_TRADING_HOST", "127.0.0.1")
    port = int(os.getenv("JARVIS_TRADING_PORT", "8016"))
    uvicorn.run("jarvis_autonomous_trading_bot.app:app", host=host, port=port, reload=False)
