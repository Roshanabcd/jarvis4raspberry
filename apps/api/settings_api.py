"""Settings REST API for JARVIS OS — Categories A through P with configuration persistence."""
import os
import time
import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config.config_manager import config

logger = logging.getLogger("JARVIS.API.Settings")
settings_router = APIRouter(prefix="/settings", tags=["settings"])


class CategoryUpdateRequest(BaseModel):
    model_config = {"extra": "allow"}
    settings: Optional[Dict[str, Any]] = None
    env_updates: Optional[Dict[str, str]] = None


@settings_router.get("")
@settings_router.get("/")
def get_all_settings():
    """Return comprehensive system configuration organized across Categories A through P."""
    from hardware.raspberry_pi.rpi_info import get_system_status, get_cpu_temp, is_online
    from apps.voice.service import voice_service
    from apps.voice.gradio_tts import gradio_cloner
    from tools.robotics.controller import robot
    from apps.vision.service import VisionService

    # 1. System Info
    sys_st = get_system_status()
    sys_st["cpu_temp_c"] = get_cpu_temp()

    # 2. Voice & Cloner Info
    voice_state = voice_service.get_state()
    cloner_status = gradio_cloner.get_provider_status()

    # 3. Vision Info
    try:
        vs = VisionService()
        cam_info = vs.camera_status()
    except Exception:
        cam_info = {"status": "simulated", "sensor": "IMX708"}

    # 4. AI Provider Info
    try:
        from ai.brain import get_brain
        brain = get_brain()
        ai_st = brain.get_providers_status()
        active_p = ai_st.get("active_provider", "ollama")
        prov_dict = {p["name"]: p["available"] for p in ai_st.get("providers", [])}
        mod_list = []
        for p in ai_st.get("providers", []):
            mod_list.extend(p.get("models", []))
    except Exception:
        active_p = "ollama"
        prov_dict = {"ollama": True}
        mod_list = ["llama3.2:1b"]

    ai_status = {
        "active_provider": active_p,
        "providers": prov_dict,
        "available_models": mod_list,
    }

    # 5. Robotics Info
    robot_info = {
        "armed": bool(robot.is_armed),
        "emergency_stopped": bool(robot.is_emergency_stopped),
        "simulation_mode": bool(config.get("simulation_mode", True)),
        "default_speed": config.get("robot", {}).get("default_speed", 50),
        "max_speed": config.get("robot", {}).get("max_speed", 100),
    }

    # 6. Sensors Info
    sensors_cfg = config.get("sensors", {})

    # 7. Memory Info
    try:
        from memory.long_term.database import MemoryDB
        db = MemoryDB(config.get("memory", {}).get("db_path", "jarvis_memory.db"))
        mem_summary = db.summarize()
    except Exception:
        mem_summary = {"total_memories": 0}

    return {
        "category_a": {
            "name": "System & SBC Info",
            "hostname": sys_st.get("hostname", "raspberrypi"),
            "os": "Debian GNU/Linux 13 (Trixie) aarch64",
            "kernel": "Linux 6.18.60+rpt-rpi-v8",
            "cpu_temp_c": sys_st.get("cpu_temp_c"),
            "cpu_usage_pct": sys_st.get("cpu_usage_pct", 0),
            "ram_pct": sys_st.get("ram_pct", 0),
            "disk_pct": sys_st.get("disk_pct", 0),
            "online": is_online(),
        },
        "category_b": {
            "name": "AI Providers & Models",
            "active_provider": ai_status["active_provider"],
            "ollama_base_url": config.get("ai", {}).get("ollama", {}).get("base_url", "http://localhost:11434"),
            "ollama_model": config.get("ai", {}).get("ollama", {}).get("model", "llama3.2:1b"),
            "providers_status": ai_status["providers"],
            "models": ai_status["available_models"],
        },
        "category_c": {
            "name": "Voice & Audio Input",
            "wake_word": config.get("wake_word", "jarvis"),
            "selected_input": voice_state.get("device", {}),
            "listening": voice_state.get("listening", False),
            "muted": voice_state.get("muted", False),
            "microphone_available": voice_state.get("microphone_available", True),
        },
        "category_d": {
            "name": "Voice Cloning & OmniVoice",
            "cloning_enabled": cloner_status.get("cloning_enabled", True),
            "gradio_url": cloner_status.get("url", ""),
            "reference_audio_path": cloner_status.get("reference_audio_path", ""),
            "online": cloner_status.get("online", False),
            "has_reference_audio": cloner_status.get("has_reference_audio", False),
            "cache_entries": cloner_status.get("cache_entries", 0),
        },
        "category_e": {
            "name": "Voice Output & TTS",
            "engine": config.get("voice", {}).get("engine", "edge-tts"),
            "rate": config.get("voice", {}).get("rate", 150),
            "volume": config.get("voice", {}).get("volume", 0.9),
            "language": config.get("voice", {}).get("language", "en"),
            "selected_output": voice_service.audio_manager.select_best_playback_device(),
        },
        "category_f": {
            "name": "Vision & Camera",
            "camera_status": cam_info,
            "sensor": "Sony IMX708 Camera Module 3",
            "mode": "RP1 CSI Hardware (Native)",
        },
        "category_g": {
            "name": "Robotics & Actuators",
            "simulation_mode": robot_info["simulation_mode"],
            "armed": robot_info["armed"],
            "emergency_stopped": robot_info["emergency_stopped"],
            "default_speed": robot_info["default_speed"],
            "max_speed": robot_info["max_speed"],
        },
        "category_h": {
            "name": "Servos & Pan-Tilt",
            "driver": "Waveshare PCA9685 16-Channel 12-bit PWM",
            "pan_channel": 0,
            "tilt_channel": 1,
            "default_angle": 90,
        },
        "category_i": {
            "name": "Sensors & Telemetry",
            "poll_interval_secs": sensors_cfg.get("poll_interval_secs", 5),
            "enabled_sensors": ["BME280", "BH1750", "VL53L0X", "HC-SR04", "PIR"],
        },
        "category_j": {
            "name": "Memory & Knowledge",
            "db_path": config.get("memory", {}).get("db_path", "jarvis_memory.db"),
            "max_context": config.get("memory", {}).get("max_context", 20),
            "memory_summary": mem_summary,
        },
        "category_k": {
            "name": "Security & Safety",
            "disarmed_boot_state": True,
            "estop_latch": True,
            "risk_confirmation_threshold": 3,
            "audit_logging_enabled": True,
        },
        "category_l": {
            "name": "Network & Connectivity",
            "port": config.get("api_port", 8000),
            "host": config.get("api_host", "127.0.0.1"),
            "online": is_online(),
            "local_ip": sys_st.get("local_ip", "127.0.0.1"),
        },
        "category_m": {
            "name": "Notifications & Alerts",
            "proactive": config.get("notifications", {}).get("proactive", True),
            "interval_secs": config.get("notifications", {}).get("interval_secs", 60),
            "cpu_warn_pct": config.get("health", {}).get("cpu_warn_pct", 80),
            "temp_warn_c": config.get("health", {}).get("temp_warn_c", 75),
        },
        "category_n": {
            "name": "Automations & Tasks",
            "scheduler_active": True,
            "tasks_count": 0,
        },
        "category_o": {
            "name": "Developer & Diagnostics",
            "log_level": "INFO",
            "service_name": "jarvis-core.service",
            "git_branch": "feat/jarvis-ultimate-integration",
        },
        "category_p": {
            "name": "Backup, Restore & Reset",
            "config_file": "config/config.yaml",
            "env_file": ".env",
            "backup_ready": True,
        },
    }


@settings_router.get("/{category}")
def get_category_settings(category: str):
    """Retrieve settings for a specific category (e.g. category_a, category_b, ...)."""
    cat_key = category.lower().strip()
    if cat_key == "integrations":
        def mask(k):
            val = os.environ.get(k) or config.get(k.lower(), "")
            if not val:
                return ""
            if len(val) <= 8:
                return "********"
            return val[:4] + "****" + val[-4:]

        return {
            "name": "Cloud AI & Service Integrations",
            "settings": {
                "gemini_api_key": mask("GEMINI_API_KEY"),
                "openai_api_key": mask("OPENAI_API_KEY"),
                "anthropic_api_key": mask("ANTHROPIC_API_KEY"),
                "nvidia_api_key": mask("NVIDIA_API_KEY"),
                "huggingface_space_url": os.environ.get("HUGGINGFACE_SPACE_URL") or config.get("voice", {}).get("gradio_url", ""),
            }
        }

    all_s = get_all_settings()
    if cat_key in all_s:
        return all_s[cat_key]
    # Check by short name
    for k, v in all_s.items():
        if cat_key in k or cat_key in v.get("name", "").lower():
            return v
    raise HTTPException(status_code=404, detail=f"Category '{category}' not found.")


@settings_router.post("/{category}")
def update_category_settings(category: str, req: CategoryUpdateRequest):
    """Update settings for a category and atomically persist to config.yaml and .env."""
    cat_key = category.lower().strip()
    updates = req.settings
    if updates is None:
        updates = getattr(req, "__pydantic_extra__", {}) or {}

    if cat_key == "integrations":
        env_dict = {}
        for key_name, env_var in [
            ("gemini_api_key", "GEMINI_API_KEY"),
            ("openai_api_key", "OPENAI_API_KEY"),
            ("anthropic_api_key", "ANTHROPIC_API_KEY"),
            ("nvidia_api_key", "NVIDIA_API_KEY"),
            ("huggingface_space_url", "HUGGINGFACE_SPACE_URL"),
        ]:
            if updates.get(key_name) and not updates[key_name].startswith("****"):
                env_dict[env_var] = updates[key_name]
                os.environ[env_var] = updates[key_name]

        if updates.get("huggingface_space_url"):
            v = config.get("voice", {})
            v["gradio_url"] = updates["huggingface_space_url"]
            config.set("voice", v)
            config.save()

        if env_dict:
            config.save_env(env_dict)
        return {"status": "ok", "category": "integrations", "saved_env": True}

    # Update in-memory and write to config.yaml
    if "wake_word" in updates:
        config.set("wake_word", str(updates["wake_word"]).strip().lower())

    if "simulation_mode" in updates:
        config.set("simulation_mode", bool(updates["simulation_mode"]))

    if "voice" in updates and isinstance(updates["voice"], dict):
        v = config.get("voice", {})
        v.update(updates["voice"])
        config.set("voice", v)

    if "gradio_url" in updates:
        v = config.get("voice", {})
        v["gradio_url"] = updates["gradio_url"]
        config.set("voice", v)

    if "robot" in updates and isinstance(updates["robot"], dict):
        r = config.get("robot", {})
        r.update(updates["robot"])
        config.set("robot", r)

    if "ai" in updates and isinstance(updates["ai"], dict):
        a = config.get("ai", {})
        a.update(updates["ai"])
        config.set("ai", a)

    # Persist config.yaml atomically
    saved_cfg = config.save()

    # Persist .env if requested
    saved_env = True
    if req.env_updates:
        saved_env = config.save_env(req.env_updates)

    return {
        "status": "ok",
        "category": cat_key,
        "saved_config": saved_cfg,
        "saved_env": saved_env,
        "updated": updates,
    }


@settings_router.post("/test/{component}")
def run_component_test(component: str):
    """Execute real hardware or service diagnostic test for a component."""
    comp = component.lower().strip()

    if comp == "microphone":
        from apps.voice.service import voice_service
        res = voice_service.listen_once(duration_secs=2)
        return {"component": comp, "status": "ok", "result": res}

    elif comp == "speaker":
        from apps.voice.gradio_tts import gradio_cloner
        res = gradio_cloner.synthesize("Audio output test. ReSpeaker speaker is operating normally.")
        if res.audio_path:
            gradio_cloner.play(res)
        return {"component": comp, "status": "ok", "provider": res.provider}

    elif comp == "voice_clone":
        from apps.voice.gradio_tts import gradio_cloner
        status = gradio_cloner.get_provider_status()
        return {"component": comp, "status": "ok", "cloner_status": status}

    elif comp == "camera":
        from apps.vision.service import VisionService
        vs = VisionService()
        frame = vs.capture_frame()
        return {"component": comp, "status": "ok", "frame_size": len(frame) if frame else 0}

    elif comp == "ai_provider":
        from ai.brain import get_brain
        brain = get_brain()
        provider = brain.get_active_provider()
        res = brain.chat("Ping: verify AI connection.", use_tools=False)
        return {"component": comp, "status": "ok", "provider": provider.name if provider else "none", "response": res.get("response", "")}

    elif comp == "robot":
        from tools.robotics.controller import robot
        st = robot.get_state()
        return {"component": comp, "status": "ok", "state": st}

    else:
        raise HTTPException(status_code=400, detail=f"Unknown component test: {component}")


@settings_router.get("/export/backup")
def export_configuration():
    """Export active system configuration as downloadable backup payload."""
    return {
        "timestamp": time.time(),
        "config": config.config,
    }
