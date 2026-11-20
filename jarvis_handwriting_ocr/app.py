"""Standalone FastAPI runner for JARVIS Handwritten to Text Converter."""

from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .config import HandwritingOCRConfig
from .router import create_router


def create_app(config: HandwritingOCRConfig | None = None) -> FastAPI:
    app = FastAPI(
        title="JARVIS OS — Handwritten to Text Converter",
        version="1.0.0",
        description="Upload handwritten photos or draw on a live canvas to extract clean digital text.",
    )
    app.include_router(create_router(config=config))

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/handwriting-ocr")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("JARVIS_OCR_PORT", "8026"))
    uvicorn.run(app, host="0.0.0.0", port=port)
