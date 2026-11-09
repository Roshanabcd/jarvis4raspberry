"""
JARVIS Core Orchestrator — Production main.py
FastAPI application with full middleware, WebSocket, startup/shutdown lifecycle.
"""
import asyncio
import logging
import os
import threading
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config.config_manager import config

# ─── Logging setup ───────────────────────────────────────────
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("JARVIS.Core")


# ─── Lifespan (startup / shutdown) ───────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    logger.info("=" * 60)
    logger.info("  JARVIS OS — Starting up")
    logger.info("=" * 60)

    # 0. Capture running loop for WebSocket broadcasting
    try:
        import apps.api.websocket_api as ws_mod
        ws_mod._main_loop = asyncio.get_running_loop()
    except Exception as e:
        logger.warning(f"Could not bind websocket loop: {e}")

    # 1. Sensor manager
    try:
        from hardware.sensors.sensor_manager import sensor_manager  # noqa: F401
        logger.info("✓ Sensor manager initialized")
    except Exception as e:
        logger.warning(f"Sensor manager skipped: {e}")

    # 2. Voice service (background thread, non-blocking)
    voice_thread = None
    try:
        from apps.voice.service import voice_service
        voice_thread = threading.Thread(
            target=voice_service.start, daemon=True, name="VoiceService"
        )
        voice_thread.start()
        logger.info("✓ Voice service started")
    except Exception as e:
        logger.warning(f"Voice service skipped: {e}")

    # 2b. Colab OmniVoice AutoRunner (background execution of Super_Eleven_Lab_Lite_2_1.ipynb)
    try:
        from apps.voice.colab_runner import colab_runner
        colab_runner.start()
        logger.info("✓ Colab OmniVoice AutoRunner started for Super_Eleven_Lab_Lite_2_1.ipynb")
    except Exception as e:
        logger.warning(f"Colab OmniVoice AutoRunner skipped: {e}")

    # 3. Scheduler
    try:
        from tools.scheduler.task_scheduler import TaskScheduler
        scheduler = TaskScheduler()
        scheduler.start()
        app.state.scheduler = scheduler
        logger.info("✓ Scheduler started")
    except Exception as e:
        logger.warning(f"Scheduler skipped: {e}")

    # 4. Robot state machine
    try:
        from hardware.raspberry_pi.state_machine import RobotStateMachine, RobotState
        sm = RobotStateMachine(RobotState.OFFLINE)
        sm.transition(RobotState.BOOTING)
        sm.transition(RobotState.IDLE)
        app.state.robot_sm = sm
        logger.info("✓ Robot state machine: IDLE")
    except Exception as e:
        logger.warning(f"Robot SM skipped: {e}")

    logger.info("✓ JARVIS OS is ready. Dashboard → http://0.0.0.0:8000/")
    yield

    # ─── Shutdown ──────────────────────────────────────────
    logger.info("JARVIS OS — Shutting down gracefully...")
    try:
        from apps.voice.service import voice_service
        voice_service.stop()
    except Exception:
        pass
    try:
        from tools.robotics.controller import robot
        robot.emergency_stop()
        robot.stop()
        robot.disarm()
    except Exception:
        pass
    try:
        from hardware.servos.controller import ServoController
        sc = ServoController()
        for ch in range(8):
            sc.stop(ch)
    except Exception:
        pass
    logger.info("JARVIS OS — Shutdown complete.")


# ─── App factory ─────────────────────────────────────────────
app = FastAPI(
    title="JARVIS OS",
    description="Just A Rather Very Intelligent System — Raspberry Pi 5",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Routers ─────────────────────────────────────────────────
def _include(router_path: str, module: str, attr: str,
             prefix: str = "", tags: list = None) -> None:
    """Safely import and include a router, skipping on error."""
    try:
        import importlib
        mod = importlib.import_module(module)
        router = getattr(mod, attr)
        app.include_router(router, prefix=prefix, tags=tags or [])
        logger.debug(f"✓ Router: {prefix or '/'}")
    except Exception as e:
        logger.warning(f"Router {module}.{attr} skipped: {e}")


_include("", "apps.api.router",       "router",       prefix="",         tags=["core"])
_include("", "apps.api.robot_api",    "robot_router", prefix="/api",     tags=["robot"])
_include("", "apps.api.memory_api",   "memory_router",prefix="/api",     tags=["memory"])
_include("", "apps.api.voice_api",    "voice_router", prefix="/api",     tags=["voice"])
_include("", "apps.api.omnivoice_api","omnivoice_router", prefix="/api", tags=["omnivoice"])
_include("", "apps.api.vision_api",   "vision_router",prefix="/api",     tags=["vision"])
_include("", "apps.api.sensors_api",  "sensors_router", prefix="/api",   tags=["sensors"])
_include("", "apps.api.sensors_api",  "sensors_router", prefix="",      tags=["sensors"])
_include("", "apps.api.chat_api",     "chat_router",  prefix="/api",     tags=["chat"])
_include("", "apps.api.logs_api",     "logs_router",  prefix="/api",     tags=["logs"])
_include("", "apps.api.settings_api", "settings_router", prefix="/api", tags=["settings"])
_include("", "apps.api.tools_api",    "tools_router",   prefix="/api", tags=["tools"])
_include("", "apps.api.scheduler_api","scheduler_router", prefix="/api", tags=["automations"])
_include("", "apps.api.health_api",   "health_router",prefix="/api",     tags=["health"])
_include("", "apps.api.diagnostics_api","diag_router",prefix="/api",     tags=["diagnostics"])
_include("", "apps.api.desktop_api",  "desktop_router",prefix="/api",    tags=["desktop"])
_include("", "apps.api.terminal_api", "terminal_router",prefix="/api",   tags=["terminal"])
_include("", "apps.api.browser_media_api", "browser_media_router", prefix="/api", tags=["browser_media"])
_include("", "apps.api.agent_orchestrator_api", "agents_router", prefix="/api", tags=["agents"])
_include("", "apps.api.computer_api", "router", prefix="", tags=["computer"])
_include("", "apps.api.websocket_api","ws_router",    prefix="",         tags=["ws"])


# ─── Static dashboard ────────────────────────────────────────
_dashboard_dir = os.path.join(os.path.dirname(__file__), "..", "dashboard", "static")
if os.path.isdir(_dashboard_dir):
    app.mount("/", StaticFiles(directory=_dashboard_dir, html=True), name="dashboard")
    logger.info(f"✓ Dashboard at {_dashboard_dir}")
else:
    logger.warning("Dashboard static directory not found — skipping mount.")


if __name__ == "__main__":
    port = int(config.get("api_port", 8000))
    uvicorn.run(
        "apps.core.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level=log_level.lower(),
        access_log=True,
    )
