"""Standalone FastAPI runner for JARVIS Document Question Answering."""

from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .config import DocumentQAConfig
from .router import create_router


def create_app(config: DocumentQAConfig | None = None) -> FastAPI:
    app = FastAPI(
        title="JARVIS OS — Document Question Answering",
        version="1.0.0",
        description="Upload, index, search, and perform semantic QA over PDF, Markdown, and text documents.",
    )
    app.include_router(create_router(config=config))

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/doc-qa")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("JARVIS_DOCQA_PORT", "8020"))
    uvicorn.run(app, host="0.0.0.0", port=port)
