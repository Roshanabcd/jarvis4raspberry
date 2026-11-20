"""Authorization policy for optional external voice-provider controls.

Starting a remote Colab workload, registering an external Gradio endpoint, or
testing a cloned remote voice can transmit data outside the device.  These
operations therefore remain off by default and require a fresh administrator
PIN plus a deliberate acknowledgement for each HTTP request.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Header, HTTPException

from config.config_manager import config
from tools.identity.user_manager import user_manager


EXTERNAL_VOICE_CONFIRMATION_VALUE = "external-voice-provider"


def _manual_remote_voice_control_enabled() -> bool:
    voice_cfg = config.get("voice", {}) if hasattr(config, "get") else {}
    return bool((voice_cfg or {}).get("colab_manual_control_enabled", False))


def require_external_voice_control(
    x_jarvis_admin_pin: Optional[str] = Header(default=None),
    x_jarvis_external_voice_confirmation: Optional[str] = Header(default=None),
) -> None:
    """FastAPI dependency for an explicitly authorized external voice action."""
    if not _manual_remote_voice_control_enabled():
        raise HTTPException(
            status_code=403,
            detail="External voice-provider control is disabled by configuration.",
        )
    if x_jarvis_external_voice_confirmation != EXTERNAL_VOICE_CONFIRMATION_VALUE:
        raise HTTPException(
            status_code=428,
            detail="Explicit external-voice-provider confirmation is required.",
        )
    if not x_jarvis_admin_pin:
        raise HTTPException(status_code=401, detail="Fresh administrator PIN is required.")

    valid, message = user_manager.verify_admin_pin(x_jarvis_admin_pin)
    if not valid:
        raise HTTPException(status_code=401, detail=f"Administrator verification failed: {message}")
