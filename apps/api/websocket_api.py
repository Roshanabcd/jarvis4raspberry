"""JARVIS WebSocket API — live telemetry at /ws"""
import asyncio, time, logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("JARVIS.API.WebSocket")
ws_router = APIRouter(tags=["ws"])

@ws_router.websocket("/ws")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket client connected.")
    try:
        while True:
            try:
                from hardware.raspberry_pi.rpi_info import get_system_status
                sys_data = get_system_status()
            except Exception:
                sys_data = {"cpu_usage_pct": 0, "ram_pct": 0, "temp_c": None, "disk_pct": 0}
            try:
                from tools.robotics.controller import robot
                robot_state = getattr(robot, "state", "UNKNOWN")
            except Exception:
                robot_state = "UNKNOWN"
            payload = {
                "cpu_pct":    sys_data.get("cpu_usage_pct", 0),
                "ram_pct":    sys_data.get("ram_pct", 0),
                "temp_c":     sys_data.get("temp_c"),
                "disk_pct":   sys_data.get("disk_pct", 0),
                "robot_state": robot_state,
                "ai_provider": "ollama",
                "voice_state": "LISTENING",
                "timestamp":  time.time(),
            }
            await websocket.send_json(payload)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
