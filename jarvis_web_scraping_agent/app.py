"""Standalone FastAPI entry point for Autonomous Web Scraping Agent."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .config import WebScraperConfig
from .router import create_router


def create_app(config: Optional[WebScraperConfig] = None) -> FastAPI:
    app = FastAPI(
        title="JARVIS OS — Autonomous Web Scraping Agent",
        version="1.0.0",
        description="Policy-compliant website data extraction, HTML structure parsing, scheduled change monitoring, and JSON export.",
    )
    app.include_router(create_router(config=config))

    @app.get("/", include_in_schema=False)
    async def root_redirect() -> RedirectResponse:
        return RedirectResponse(url="/web-scraper")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("JARVIS_SCRAPER_HOST", "127.0.0.1")
    port = int(os.getenv("JARVIS_SCRAPER_PORT", "8017"))
    uvicorn.run("jarvis_web_scraping_agent.app:app", host=host, port=port, reload=False)
