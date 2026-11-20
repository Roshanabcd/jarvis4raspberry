"""Standalone FastAPI entry point for AI Content Creation Pipeline."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .config import ContentPipelineConfig
from .router import create_router


def create_app(config: Optional[ContentPipelineConfig] = None) -> FastAPI:
    app = FastAPI(
        title="JARVIS OS — AI Content Creation Pipeline",
        version="1.0.0",
        description="End-to-end creative writing assistant for technical blogs, short-video scripts, hooks, captions, and carousel outlines.",
    )
    app.include_router(create_router(config=config))

    @app.get("/", include_in_schema=False)
    async def root_redirect() -> RedirectResponse:
        return RedirectResponse(url="/content-pipeline")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("JARVIS_CONTENT_HOST", "127.0.0.1")
    port = int(os.getenv("JARVIS_CONTENT_PORT", "8012"))
    uvicorn.run("jarvis_ai_content_pipeline.app:app", host=host, port=port, reload=False)
