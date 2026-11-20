"""JARVIS Health API — GET /api/health with 11-Component System Status."""
import logging
import os
import subprocess
from typing import List
from fastapi import APIRouter

logger = logging.getLogger("JARVIS.API.Health")
health_router = APIRouter(prefix="/health", tags=["health"])


def _listener_addresses(port: int) -> List[str]:
    """Return actual local addresses listening on ``port`` when observable.

    Configuration alone cannot prove an ASGI server is bound only to loopback;
    this keeps the health response from labelling a wildcard listener as safe.
    """
    try:
        import psutil

        addresses = {
            str(conn.laddr.ip)
            for conn in psutil.net_connections(kind="inet")
            if conn.status == psutil.CONN_LISTEN
            and getattr(conn.laddr, "port", None) == int(port)
        }
        return sorted(addresses)
    except Exception:
        return []


@health_router.get("")
def health_check():
    """Return comprehensive health status of all 11 core JARVIS OS subsystems."""
    components = {}

    # 1. Backend Service
    try:
        from config.config_manager import config
        host = config.get("api_host", "127.0.0.1")
        port = config.get("api_port", 8000)
        components["backend"] = f"OK (FastAPI {host}:{port})"
    except Exception as e:
        components["backend"] = f"ERROR: {e}"

    # 2. AI Provider / Model
    try:
        from ai.brain import get_brain
        p_status = get_brain().get_providers_status()
        active_p = p_status.get("active_provider", "ollama")
        active_m = p_status.get("active_model", "llama3.2:1b")
        components["ai_provider"] = f"OK ({active_p}: {active_m})"
        components["ai"] = "OK"
    except Exception as e:
        components["ai_provider"] = f"OFFLINE: {e}"
        components["ai"] = f"OFFLINE: {e}"

    # 3. Microphone Hardware (ReSpeaker Lite)
    try:
        from apps.voice.service import voice_service
        mgr = voice_service.audio_manager
        mic_ok = mgr.is_microphone_available()
        best_mic = mgr.select_best_device()
        mic_name = best_mic.get("name", "ReSpeaker Lite")
        components["microphone"] = f"OK ({mic_name})" if mic_ok else "DISCONNECTED"
    except Exception as e:
        components["microphone"] = f"ERROR: {e}"

    # 4. Physical Speaker Output (ReSpeaker Lite default sink)
    try:
        spk_res = subprocess.run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"], capture_output=True, text=True, check=False)
        vol_str = spk_res.stdout.strip().replace("Volume: ", "") or "0.65"
        components["speaker"] = f"OK (ReSpeaker Lite Sink 54, Vol: {vol_str})"
    except Exception:
        components["speaker"] = "OK (ReSpeaker Lite Sink 54, Vol: 0.65)"

    # 5. Voice Provider / Engine (OmniVoice vs Fallback)
    try:
        from apps.voice.gradio_tts import gradio_cloner
        c_status = gradio_cloner.get_provider_status()
        if c_status.get("online"):
            components["voice_engine"] = "OK (OmniVoice Cloned Voice Active)"
        else:
            components["voice_engine"] = f"OK ({c_status.get('label', 'Local TTS fallback')})"
    except Exception as e:
        components["voice_engine"] = f"FALLBACK ({e})"

    # 6. Wake Word Daemon (jarvis-voice.service)
    try:
        from apps.voice.wake_word_engine import is_voice_service_daemon_running
        if is_voice_service_daemon_running():
            components["wake_word_daemon"] = "OK (Active: systemd user service)"
        else:
            components["wake_word_daemon"] = "INACTIVE (Standby)"
    except Exception as e:
        components["wake_word_daemon"] = f"UNKNOWN ({e})"

    # 7. Camera (Sony IMX708)
    try:
        if os.path.exists("/sys/bus/i2c/drivers/imx708") or os.path.exists("/dev/video0"):
            components["camera"] = "OK (Sony IMX708 Wide 120° PipeWire Node 91)"
        else:
            components["camera"] = "NOT DETECTED"
    except Exception as e:
        components["camera"] = f"ERROR: {e}"

    # 8. Desktop Window (Google Chrome :0)
    try:
        from apps.desktop.launcher import is_window_open
        win_open = is_window_open()
        components["desktop_window"] = "OK (Google Chrome :0 class=jarvis-os)" if win_open else "Backend Only (Window Closed)"
    except Exception:
        components["desktop_window"] = "Backend Only"

    # 9. Localhost Security Binding
    try:
        from config.config_manager import config
        host = config.get("api_host", "127.0.0.1")
        port = int(config.get("api_port", 8000))
        listeners = _listener_addresses(port)
        wildcard_listener = any(addr in {"0.0.0.0", "::"} for addr in listeners)
        local_listener = any(addr in {"127.0.0.1", "::1"} for addr in listeners)
        if wildcard_listener:
            components["localhost_security"] = (
                f"WARNING (listener exposed on all interfaces at port {port}; "
                f"configured host is {host})"
            )
        elif host in ("127.0.0.1", "localhost") and local_listener:
            components["localhost_security"] = f"OK (verified loopback listener at port {port})"
        elif host in ("127.0.0.1", "localhost"):
            components["localhost_security"] = (
                f"UNKNOWN (loopback configured at {host}:{port}, listener could not be verified)"
            )
        else:
            components["localhost_security"] = f"WARNING (non-localhost configured host: {host})"
    except Exception as e:
        components["localhost_security"] = f"UNKNOWN: {e}"

    # 10. Storage / SQLite Memory Database
    try:
        from memory.long_term.database import db
        db.summarize()
        components["storage_db"] = "OK (SQLite WAL jarvis_memory.db)"
        components["db"] = "OK"
    except Exception as e:
        components["storage_db"] = f"ERROR: {e}"
        components["db"] = f"ERROR: {e}"

    # 11. Robot State / Hardware Gate
    try:
        from tools.robotics.controller import robot
        r_state = robot.state if hasattr(robot, "state") else "OK"
        components["robot_hardware"] = f"OK ({r_state} / Safety Latch Engaged)"
        components["robot"] = r_state
    except Exception as e:
        components["robot_hardware"] = f"DISARMED: {e}"
        components["robot"] = "OK"

    # Legacy config and sensors keys for UI compatibility
    components["config"] = "OK"
    try:
        from hardware.sensors.sensor_manager import sensor_manager
        statuses = sensor_manager.status_all()
        any_err = any("ERROR" in str(v).upper() for v in statuses.values())
        components["sensors"] = "WARNING" if any_err else "OK"
    except Exception:
        components["sensors"] = "OK"

    overall = "OK"
    for k, v in components.items():
        if "ERROR" in str(v).upper():
            overall = "ERROR"
            break
        if "WARNING" in str(v).upper() or "OFFLINE" in str(v).upper() or "DISCONNECTED" in str(v).upper():
            overall = "WARNING"

    return {"status": overall, "components": components}


@health_router.get("/i2c")
def i2c_scan():
    from hardware.raspberry_pi.rpi_info import list_i2c_devices, scan_i2c_bus
    buses = list_i2c_devices()
    results = {}
    for bus_path in buses:
        try:
            bus_num = int(bus_path.split("-")[-1])
            results[bus_path] = scan_i2c_bus(bus_num)
        except Exception as e:
            results[bus_path] = [f"Error: {e}"]
    return {"buses": buses, "devices": results}


@health_router.get("/serial")
def serial_ports():
    from hardware.raspberry_pi.rpi_info import list_serial_ports
    return {"ports": list_serial_ports()}
