"""Cross-process speaker playback state for JARVIS OS.

Allows background voice capture daemon and FastAPI backend to share active
speaker playback status, eliminating acoustic feedback loops when JARVIS speaks aloud.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import tempfile
import time
import uuid
from typing import Optional

logger = logging.getLogger("JARVIS.Voice.PlaybackState")


def default_playback_path() -> Path:
    return Path(f"/run/user/{os.getuid()}/jarvis/playback-active.json")


def set_playback_active(
    active: bool,
    *,
    duration_hint_s: float = 10.0,
    path: Optional[Path | str] = None,
    lease_id: Optional[str] = None,
) -> bool:
    """Publish current audio playback lease across process boundaries."""
    target = Path(path) if path is not None else default_playback_path()
    try:
        if not active:
            if target.is_file():
                if lease_id is None:
                    target.unlink(missing_ok=True)
                else:
                    with target.open(encoding="utf-8") as stream:
                        current = json.load(stream)
                    if current.get("lease_id") == lease_id:
                        target.unlink(missing_ok=True)
            return True

        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".playback-", dir=target.parent)
        now = time.time()
        payload = {
            "playing": True,
            "pid": os.getpid(),
            "timestamp": now,
            "expires_at": now + max(1.0, float(duration_hint_s)),
            "lease_id": lease_id or uuid.uuid4().hex,
        }
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream)
        os.replace(temporary, target)
        return True
    except OSError as exc:
        logger.debug("Failed to set cross-process playback state: %s", exc)
        return False


def is_playback_active(
    *,
    path: Optional[Path | str] = None,
    now: Optional[float] = None,
    check_local: bool = True,
) -> bool:
    """Check if any JARVIS process is actively playing audio through physical speakers."""
    # Check in-process speech manager if reachable and no custom IPC path requested
    if check_local and path is None:
        try:
            from apps.voice.speech_manager import speech_manager
            if speech_manager.is_playing():
                return True
        except Exception:
            pass

    target = Path(path) if path is not None else default_playback_path()
    if not target.is_file():
        return False

    current_time = time.time() if now is None else now
    try:
        with target.open("r", encoding="utf-8") as stream:
            raw = stream.read(512)
        data = json.loads(raw)
        if not data.get("playing"):
            return False
        timestamp = data.get("timestamp", 0.0)
        expires_at = data.get("expires_at", 0.0)
        # Verify freshness
        if not (0 <= (current_time - timestamp) <= 30.0):
            return False
        if current_time >= expires_at:
            return False
        return True
    except (OSError, ValueError, TypeError) as exc:
        logger.debug("Could not verify cross-process playback state: %s", exc)
        return False
