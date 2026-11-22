"""Standalone FastAPI runner for JARVIS Fraud Detection System."""

from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .config import FraudDetectionConfig
from .router import create_router


def create_app(config: FraudDetectionConfig | None = None) -> FastAPI:
    app = FastAPI(
        title="JARVIS OS — Fraud Detection System",
        version="1.0.0",
        description="Anomaly detection and suspicious pattern analysis across transactions, auth logs, and audit entries.",
    )
    app.include_router(create_router(config=config))

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/fraud-detection")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("JARVIS_FRAUD_PORT", "8022"))
    uvicorn.run(app, host="0.0.0.0", port=port)
