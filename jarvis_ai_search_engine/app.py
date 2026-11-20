"""Standalone FastAPI runner for JARVIS End-to-End AI Search Engine."""

from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .config import AISearchConfig
from .router import create_router


def create_app(config: AISearchConfig | None = None) -> FastAPI:
    app = FastAPI(
        title="JARVIS OS — End-to-End AI Search Engine",
        version="1.0.0",
        description="Unified semantic indexing and neural hybrid RRF search over documents, logs, codebases, and web knowledge.",
    )
    app.include_router(create_router(config=config))

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/ai-search")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("JARVIS_SEARCH_PORT", "8021"))
    uvicorn.run(app, host="0.0.0.0", port=port)
