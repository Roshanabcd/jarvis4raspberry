"""Standalone FastAPI entry point for AI Study Planner."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .config import StudyPlannerConfig
from .router import create_router


def create_app(config: Optional[StudyPlannerConfig] = None) -> FastAPI:
    app = FastAPI(
        title="JARVIS OS — AI Study Planner",
        version="1.0.0",
        description="Personalized study scheduling, learning goal breakdown, SM-2 spaced-repetition tracking, and syllabus milestone management.",
    )
    app.include_router(create_router(config=config))

    @app.get("/", include_in_schema=False)
    async def root_redirect() -> RedirectResponse:
        return RedirectResponse(url="/study-planner")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("JARVIS_STUDY_HOST", "127.0.0.1")
    port = int(os.getenv("JARVIS_STUDY_PORT", "8015"))
    uvicorn.run("jarvis_ai_study_planner.app:app", host=host, port=port, reload=False)
