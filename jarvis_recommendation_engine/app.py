"""Standalone FastAPI runner for JARVIS Deep Learning Recommendation Engine."""

from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .config import RecommendationConfig
from .router import create_router


def create_app(config: RecommendationConfig | None = None) -> FastAPI:
    app = FastAPI(
        title="JARVIS OS — Deep Learning Recommendation Engine",
        version="1.0.0",
        description="Hybrid 128-D neural embedding + collaborative filtering + SGD latent-factor recommender.",
    )
    app.include_router(create_router(config=config))

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/recommendations")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("JARVIS_REC_PORT", "8019"))
    uvicorn.run(app, host="0.0.0.0", port=port)
