"""Standalone FastAPI entry point for AI Social Media Automation."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .config import SocialAutomationConfig
from .router import create_router


def create_app(config: Optional[SocialAutomationConfig] = None) -> FastAPI:
    app = FastAPI(
        title="JARVIS OS — AI Social Media Automation",
        version="1.0.0",
        description="Multi-platform content planning, automated copy generation, scheduled publishing workflows, and engagement analytics.",
    )
    app.include_router(create_router(config=config))

    @app.get("/", include_in_schema=False)
    async def root_redirect() -> RedirectResponse:
        return RedirectResponse(url="/social-automation")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("JARVIS_SOCIAL_HOST", "127.0.0.1")
    port = int(os.getenv("JARVIS_SOCIAL_PORT", "8014"))
    uvicorn.run("jarvis_ai_social_automation.app:app", host=host, port=port, reload=False)
