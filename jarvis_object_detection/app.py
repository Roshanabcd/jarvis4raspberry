"""Standalone FastAPI runner for JARVIS Real-Time Object Detection."""

from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .config import ObjectDetectionConfig
from .router import create_router


def create_app(config: ObjectDetectionConfig | None = None) -> FastAPI:
    app = FastAPI(
        title="JARVIS OS — Real-Time Object Detection",
        version="1.0.0",
        description="Real-time object detection, centroid tracking, ROI intrusion zones, and live camera WebSocket HUD.",
    )
    app.include_router(create_router(config=config))

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/object-detection")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("JARVIS_OBJDET_PORT", "8027"))
    uvicorn.run(app, host="0.0.0.0", port=port)
