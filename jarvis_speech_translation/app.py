"""Standalone FastAPI runner for JARVIS Real-Time Speech Translation."""

from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .config import SpeechTranslationConfig
from .router import create_router


def create_app(config: SpeechTranslationConfig | None = None) -> FastAPI:
    app = FastAPI(
        title="JARVIS OS — Real-Time Speech Translation",
        version="1.0.0",
        description="Continuous bilingual speech recognition, translation, WebSocket streaming, and voice playback.",
    )
    app.include_router(create_router(config=config))

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/speech-translation")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("JARVIS_TRANSLATE_PORT", "8024"))
    uvicorn.run(app, host="0.0.0.0", port=port)
