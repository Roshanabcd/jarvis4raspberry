"""JARVIS production ASGI entry point.

The factory lives separately so focused tests can construct a narrow app without
importing every router or starting the production hardware lifecycle.
"""

import logging
import os

import uvicorn

from apps.core.app_factory import create_app, production_lifespan
from config.config_manager import config


log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Preserve the historical public name for code importing ``main.lifespan``.
lifespan = production_lifespan
app = create_app()


if __name__ == "__main__":
    port = int(config.get("api_port", 8000))
    host = str(config.get("api_host", "127.0.0.1"))
    uvicorn.run(
        "apps.core.main:app",
        host=host,
        port=port,
        reload=False,
        log_level=log_level.lower(),
        access_log=True,
    )
