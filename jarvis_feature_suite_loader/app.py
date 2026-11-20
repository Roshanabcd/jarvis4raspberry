"""Standalone FastAPI runner serving the Unified JARVIS Feature Suite on port 8010."""

from __future__ import annotations

import os
from typing import List, Optional

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .loader import mount_jarvis_feature_suite


def create_app(enabled_packages: Optional[List[str]] = None) -> FastAPI:
    app = FastAPI(
        title="JARVIS OS — Unified Feature Suite",
        version="1.0.0",
        description="Unified launchpad mounting all 16 additive JARVIS OS feature modules.",
    )
    mount_jarvis_feature_suite(app, enabled_packages=enabled_packages)

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/suite")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("JARVIS_SUITE_PORT", "8010"))
    uvicorn.run(app, host="0.0.0.0", port=port)
