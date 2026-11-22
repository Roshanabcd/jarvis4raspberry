"""Standalone FastAPI entry point for AI Interview Bot."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .config import InterviewBotConfig
from .router import create_router


def create_app(config: Optional[InterviewBotConfig] = None) -> FastAPI:
    app = FastAPI(
        title="JARVIS OS — AI Interview Bot",
        version="1.0.0",
        description="Interactive technical and behavioral interview simulation with dynamic questioning, evaluation scoring, and feedback reports.",
    )
    app.include_router(create_router(config=config))

    @app.get("/", include_in_schema=False)
    async def root_redirect() -> RedirectResponse:
        return RedirectResponse(url="/interview-bot")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("JARVIS_INTERVIEW_HOST", "127.0.0.1")
    port = int(os.getenv("JARVIS_INTERVIEW_PORT", "8013"))
    uvicorn.run("jarvis_ai_interview_bot.app:app", host=host, port=port, reload=False)
