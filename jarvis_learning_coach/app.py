"""Standalone FastAPI runner for JARVIS Personalized Learning AI Coach."""

from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .config import LearningCoachConfig
from .router import create_router


def create_app(config: LearningCoachConfig | None = None) -> FastAPI:
    app = FastAPI(
        title="JARVIS OS — Personalized Learning AI Coach",
        version="1.0.0",
        description="Adaptive Socratic tutoring, concept mastery diagnostics, and personalized exercises.",
    )
    app.include_router(create_router(config=config))

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/learning-coach")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("JARVIS_COACH_PORT", "8023"))
    uvicorn.run(app, host="0.0.0.0", port=port)
