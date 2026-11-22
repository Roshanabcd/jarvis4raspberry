"""JARVIS WebSocket API — live telemetry and chat synchronization at /ws"""
import asyncio, time, logging
from typing import Set, Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("JARVIS.API.WebSocket")
ws_router = APIRouter(tags=["ws"])

_active_connections: Set[WebSocket] = set()
_main_loop: Optional[asyncio.AbstractEventLoop] = None


async def broadcast_event(event_dict: Dict[str, Any]) -> None:
    """Send event to all active connected clients."""
    disconnected = set()
    for ws in list(_active_connections):
        try:
            await ws.send_json(event_dict)
        except Exception:
            disconnected.add(ws)
    for ws in disconnected:
        _active_connections.discard(ws)


def broadcast_chat_message(
    role: str,
    text: str,
    audio_url: Optional[str] = None,
    message_id: Optional[str] = None,
    turn_id: Optional[str] = None,
    playback_target: str = "browser",
    provider_label: Optional[str] = None,
    is_cloned: bool = False,
) -> None:
    """Thread-safe trigger to broadcast dialogue turn to connected dashboard web clients."""
    global _main_loop
    payload = {
        "type": "chat_message",
        "role": role,
        "text": text,
        "audio_url": audio_url,
        "message_id": message_id or turn_id,
        "turn_id": turn_id or message_id,
        "playback_target": playback_target,
        "provider_label": provider_label,
        "is_cloned": is_cloned,
        "timestamp": time.time(),
    }
    if _main_loop and _main_loop.is_running():
        asyncio.run_coroutine_threadsafe(broadcast_event(payload), _main_loop)


def broadcast_voice_state(
    state: str,
    detail: Optional[str] = None,
    mic_level: Optional[float] = None,
) -> None:
    """Thread-safe trigger to broadcast live voice state transitions over WebSocket."""
    global _main_loop
    payload = {
        "type": "voice_status",
        "state": state,
        "detail": detail,
        "mic_level": mic_level,
        "timestamp": time.time(),
    }
    if _main_loop and _main_loop.is_running():
        asyncio.run_coroutine_threadsafe(broadcast_event(payload), _main_loop)


def broadcast_voice_stage(
    stage: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Thread-safe trigger to broadcast live voice stages (Listening, Heard, Thinking, Speaking, Ready) over WebSocket."""
    global _main_loop
    payload = {
        "type": "voice_stage",
        "stage": stage,
        **(details or {}),
        "timestamp": time.time(),
    }
    if _main_loop and _main_loop.is_running():
        asyncio.run_coroutine_threadsafe(broadcast_event(payload), _main_loop)



@ws_router.websocket("/ws")
async def websocket_telemetry(websocket: WebSocket):
    global _main_loop
    _main_loop = asyncio.get_running_loop()
    await websocket.accept()
    _active_connections.add(websocket)
    logger.info("WebSocket client connected. Total clients: %d", len(_active_connections))
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
            mic_level = None
            try:
                from apps.voice.service import voice_service
                voice_info = voice_service.get_state()
                voice_state = voice_info["state"]
                mic_level = (voice_info.get("wake_engine") or {}).get("audio_level_rms")
            except Exception:
                voice_state = "STANDBY"

            try:
                from ai.providers.base import ai_providers
                active_prov = getattr(ai_providers, "active_provider_name", "ollama")
            except Exception:
                active_prov = "ollama"

            payload = {
                "type":        "telemetry",
                "cpu_pct":    sys_data.get("cpu_usage_pct", 0),
                "ram_pct":    sys_data.get("ram_pct", 0),
                "temp_c":     sys_data.get("temp_c"),
                "disk_pct":   sys_data.get("disk_pct", 0),
                "robot_state": robot_state,
                "ai_provider": active_prov,
                "voice_state": voice_state,
                "mic_level":   mic_level,
                "timestamp":  time.time(),
            }
            await websocket.send_json(payload)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        _active_connections.discard(websocket)
        logger.info("WebSocket client disconnected. Total clients: %d", len(_active_connections))
    except Exception as e:
        _active_connections.discard(websocket)
        logger.error(f"WebSocket error: {e}")
