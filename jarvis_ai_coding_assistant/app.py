"""Standalone FastAPI entry point for running AI Coding Assistant independently."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .config import CodingAssistantConfig
from .router import create_router


def create_app(config: Optional[CodingAssistantConfig] = None) -> FastAPI:
    app = FastAPI(
        title="JARVIS OS — AI Coding Assistant",
        version="1.0.0",
        description="Intelligent code generation, refactoring, security static analysis, and automated test synthesis.",
    )
    app.include_router(create_router(config=config))

    @app.get("/", include_in_schema=False)
    async def root_redirect() -> RedirectResponse:
        return RedirectResponse(url="/coding-assistant")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("JARVIS_CODING_HOST", "127.0.0.1")
    port = int(os.getenv("JARVIS_CODING_PORT", "8011"))
    uvicorn.run("jarvis_ai_coding_assistant.app:app", host=host, port=port, reload=False)
