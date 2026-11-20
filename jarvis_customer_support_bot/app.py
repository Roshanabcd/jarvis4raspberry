"""Standalone FastAPI entry point for Customer Support Bot."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .config import SupportBotConfig
from .router import create_router


def create_app(config: Optional[SupportBotConfig] = None) -> FastAPI:
    app = FastAPI(
        title="JARVIS OS — ChatGPT-Powered Customer Support Bot",
        version="1.0.0",
        description="Domain-specific customer inquiry answering, ticket triage, sentiment classification, and escalation routing.",
    )
    app.include_router(create_router(config=config))

    @app.get("/", include_in_schema=False)
    async def root_redirect() -> RedirectResponse:
        return RedirectResponse(url="/support-bot")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("JARVIS_SUPPORT_HOST", "127.0.0.1")
    port = int(os.getenv("JARVIS_SUPPORT_PORT", "8018"))
    uvicorn.run("jarvis_customer_support_bot.app:app", host=host, port=port, reload=False)
