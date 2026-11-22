"""Standalone FastAPI runner for JARVIS Smart Resume Matching."""

from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .config import ResumeMatchingConfig
from .router import create_router


def create_app(config: ResumeMatchingConfig | None = None) -> FastAPI:
    app = FastAPI(
        title="JARVIS OS — Smart Resume Matching",
        version="1.0.0",
        description="Automated skill extraction, candidate qualification scoring, and semantic gap analysis.",
    )
    app.include_router(create_router(config=config))

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/resume-matching")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("JARVIS_RESUME_PORT", "8025"))
    uvicorn.run(app, host="0.0.0.0", port=port)
