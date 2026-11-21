"""Factory functions for production and hardware-safe JARVIS FastAPI apps.

Production still installs every router and runs the full service lifecycle.
Focused tests can instead pass a narrow router list with ``noop_lifespan`` so
they do not claim sensor, microphone, camera, I2C, or serial resources merely
by constructing an application.
"""

from __future__ import annotations

import asyncio
import importlib
import logging
import os
import threading
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Sequence, Tuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from config.config_manager import config

logger = logging.getLogger("JARVIS.Core")

RouterSpec = Tuple[str, str, str, Tuple[str, ...]]


# Kept as data so tests can select only the router that they exercise.  The
# modules themselves are not imported until ``create_app`` includes a spec.
DEFAULT_ROUTER_SPECS: Tuple[RouterSpec, ...] = (
    ("apps.api.router", "router", "", ("core",)),
    ("apps.api.robot_api", "robot_router", "/api", ("robot",)),
    ("apps.api.memory_api", "memory_router", "/api", ("memory",)),
    ("apps.api.voice_api", "voice_router", "/api", ("voice",)),
    ("apps.api.omnivoice_api", "omnivoice_router", "/api", ("omnivoice",)),
    ("apps.api.vision_api", "vision_router", "/api", ("vision",)),
    ("apps.api.sensors_api", "sensors_router", "/api", ("sensors",)),
    ("apps.api.sensors_api", "sensors_router", "", ("sensors",)),
    ("apps.api.active_desktop_api", "router", "", ("active_desktop",)),
    ("apps.api.chat_api", "chat_router", "/api", ("chat",)),
    ("apps.api.task_jobs_api", "router", "", ("task_jobs",)),
    ("apps.api.logs_api", "logs_router", "/api", ("logs",)),
    ("apps.api.settings_api", "settings_router", "/api", ("settings",)),
    ("apps.api.tools_api", "tools_router", "/api", ("tools",)),
    ("apps.api.scheduler_api", "scheduler_router", "/api", ("automations",)),
    ("apps.api.health_api", "health_router", "/api", ("health",)),
    ("apps.api.diagnostics_api", "diag_router", "/api", ("diagnostics",)),
    ("apps.api.desktop_api", "desktop_router", "/api", ("desktop",)),
    ("apps.api.terminal_api", "terminal_router", "/api", ("terminal",)),
    ("apps.api.identity_api", "identity_router", "/api", ("identity",)),
    ("apps.api.account_api", "account_router", "/api", ("account",)),
    ("apps.api.apps_center_api", "apps_center_router", "/api", ("apps_center",)),
    ("apps.api.browser_media_api", "browser_media_router", "/api", ("browser_media",)),
    ("apps.api.agent_orchestrator_api", "agents_router", "/api", ("agents",)),
    ("apps.api.hybrid_developer_api", "developer_router", "/api", ("developer",)),
    ("apps.api.youtube_api", "youtube_router", "/api", ("youtube",)),
    ("apps.api.research_api", "research_router", "/api", ("research",)),
    ("apps.api.document_qa_api", "document_qa_router", "/api", ("document_qa",)),
    ("apps.api.computer_api", "router", "", ("computer",)),
    ("apps.api.websocket_api", "ws_router", "", ("ws",)),
)


@asynccontextmanager
async def production_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Run the explicitly production-only service lifecycle."""
    logger.info("=" * 60)
    logger.info("  JARVIS OS — Starting up")
    logger.info("=" * 60)

    # 0. Capture running loop for WebSocket broadcasting.
    try:
        import apps.api.websocket_api as ws_mod

        ws_mod._main_loop = asyncio.get_running_loop()
    except Exception as exc:
        logger.warning("Could not bind websocket loop: %s", exc)

    # 1. Sensor manager.
    try:
        from hardware.sensors.sensor_manager import sensor_manager  # noqa: F401

        logger.info("✓ Sensor manager initialized")
    except Exception as exc:
        logger.warning("Sensor manager skipped: %s", exc)

    # 2. Voice service (background thread, non-blocking).
    try:
        from apps.voice.wake_word_engine import is_voice_service_daemon_running

        if is_voice_service_daemon_running():
            logger.info("✓ Background jarvis-voice.service is active; backend preserving single microphone owner.")
        else:
            from apps.voice.service import voice_service

            voice_thread = threading.Thread(
                target=voice_service.start, daemon=True, name="VoiceService"
            )
            voice_thread.start()
            logger.info("✓ Voice service started in backend process (standalone)")
    except Exception as exc:
        logger.warning("Voice service skipped: %s", exc)

    # 2b. Starting external GPU execution must never be an import side effect.
    try:
        voice_cfg = config.get("voice", {}) or {}
        if bool(voice_cfg.get("colab_autorun", False)):
            from apps.voice.colab_runner import colab_runner

            colab_runner.start()
            logger.info("✓ Colab OmniVoice AutoRunner started by explicit configuration")
        else:
            logger.info("Colab OmniVoice AutoRunner disabled (set voice.colab_autorun=true to opt in)")
    except Exception as exc:
        logger.warning("Colab OmniVoice AutoRunner skipped: %s", exc)

    # 3. Scheduler.
    try:
        from tools.scheduler.task_scheduler import TaskScheduler

        scheduler = TaskScheduler()
        scheduler.start()
        app.state.scheduler = scheduler
        logger.info("✓ Scheduler started")
    except Exception as exc:
        logger.warning("Scheduler skipped: %s", exc)

    # 4. Robot state machine.
    try:
        from hardware.raspberry_pi.state_machine import RobotStateMachine, RobotState

        sm = RobotStateMachine(RobotState.OFFLINE)
        sm.transition(RobotState.BOOTING)
        sm.transition(RobotState.IDLE)
        app.state.robot_sm = sm
        logger.info("✓ Robot state machine: IDLE")
    except Exception as exc:
        logger.warning("Robot SM skipped: %s", exc)

    logger.info("✓ JARVIS OS is ready. Dashboard → http://127.0.0.1:8000/")
    yield

    logger.info("JARVIS OS — Shutting down gracefully...")
    try:
        from apps.api.task_jobs_api import close_manager
        close_manager()
    except Exception:
        logger.warning("Background tasks interrupted during shutdown; they will not replay.")
    try:
        from apps.voice.service import voice_service

        voice_service.stop()
    except Exception:
        pass
    try:
        # Do not create a controller merely because the web process is
        # stopping.  If this process owned one, return it to a safe state.
        from tools.robotics.controller import get_existing_robot

        robot = get_existing_robot()
        if robot is not None:
            robot.emergency_stop()
            robot.stop()
            robot.disarm()
    except Exception:
        pass
    logger.info("JARVIS OS — Shutdown complete.")


@asynccontextmanager
async def noop_lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """A deliberately inert lifespan for narrow, hardware-safe test apps."""
    yield


def _include_router(app: FastAPI, spec: RouterSpec) -> None:
    """Import and attach one router without making an import failure fatal."""
    module_name, attr, prefix, tags = spec
    try:
        module = importlib.import_module(module_name)
        router = getattr(module, attr)
        app.include_router(router, prefix=prefix, tags=list(tags))
        logger.debug("✓ Router: %s", prefix or "/")
    except Exception as exc:
        logger.warning("Router %s.%s skipped: %s", module_name, attr, exc)


def create_app(
    *,
    router_specs: Sequence[RouterSpec] = DEFAULT_ROUTER_SPECS,
    lifespan_context=production_lifespan,
    include_dashboard: bool = True,
) -> FastAPI:
    """Construct a JARVIS FastAPI app with explicitly chosen side effects.

    ``router_specs=()`` and ``lifespan_context=noop_lifespan`` create a safe
    shell for focused tests.  The production entry point uses all defaults.
    """
    app = FastAPI(
        title="JARVIS OS",
        description="Just A Rather Very Intelligent System — Raspberry Pi 5",
        version="0.1.0",
        lifespan=lifespan_context,
    )
    app.add_middleware(
        CORSMiddleware,
        # Credentialed browser requests must never accept a wildcard origin.
        allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for spec in router_specs:
        _include_router(app, spec)

    try:
        from jarvis_feature_suite_loader import mount_jarvis_feature_suite

        mount_jarvis_feature_suite(app)
        logger.info("✓ JARVIS Unified Feature Suite mounted at /suite")
    except Exception as exc:
        logger.warning("JARVIS Unified Feature Suite skipped: %s", exc)

    if include_dashboard:
        futuristic_dir = os.path.join(os.path.dirname(__file__), "..", "dashboard", "futuristic")
        if os.path.isdir(futuristic_dir):
            app.mount("/futuristic", StaticFiles(directory=futuristic_dir, html=True), name="futuristic")
            logger.info("✓ Futuristic dashboard at %s", futuristic_dir)

            @app.get("/futuristic", include_in_schema=False)
            def _redirect_futuristic():
                return RedirectResponse(url="/futuristic/")

        dashboard_dir = os.path.join(os.path.dirname(__file__), "..", "dashboard", "static")
        if os.path.isdir(dashboard_dir):
            app.mount("/", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")
            logger.info("✓ Dashboard at %s", dashboard_dir)

            @app.get("/dashboard", include_in_schema=False)
            def _redirect_dashboard():
                return RedirectResponse(url="/")
        else:
            logger.warning("Dashboard static directory not found — skipping mount.")

    return app

