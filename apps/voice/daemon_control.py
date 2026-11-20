"""Cross-process voice control IPC between JARVIS core and background voice daemon.

Transmits explicit control directives (mute, unmute, stop, barge_in, push_to_talk)
via secure, permissions-checked local runtime files under /run/user/<uid>/jarvis.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import tempfile
import time
from typing import Optional

logger = logging.getLogger("JARVIS.Voice.DaemonControl")

ALLOWED_ACTIONS = frozenset({"mute", "unmute", "stop", "barge_in", "push_to_talk"})


def default_control_path() -> Path:
    return Path(f"/run/user/{os.getuid()}/jarvis/voice-control.json")


def send_daemon_command(action: str, *, path: Optional[Path | str] = None) -> bool:
    """Send a control command to the running background voice daemon."""
    act = action.strip().lower()
    if act not in ALLOWED_ACTIONS:
        logger.warning("Rejected invalid daemon action: %s", action)
        return False

    target = Path(path) if path is not None else default_control_path()
    try:
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".voice-ctrl-", dir=target.parent)
        payload = {
            "action": act,
            "timestamp": time.time(),
            "pid": os.getpid(),
        }
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream)
        os.replace(temporary, target)
        logger.debug("Dispatched daemon command '%s' to %s", act, target)
        return True
    except OSError as exc:
        logger.warning("Could not dispatch daemon command '%s': %s", act, exc)
        return False


def poll_daemon_command(*, path: Optional[Path | str] = None, max_age_secs: float = 5.0) -> Optional[str]:
    """Poll and consume any pending fresh control command destined for this daemon process."""
    target = Path(path) if path is not None else default_control_path()
    if not target.is_file():
        return None

    try:
        with target.open("r", encoding="utf-8") as stream:
            raw = stream.read(512)
        target.unlink(missing_ok=True)
        data = json.loads(raw)
        act = data.get("action")
        timestamp = data.get("timestamp")
        if not isinstance(act, str) or act not in ALLOWED_ACTIONS:
            return None
        if not isinstance(timestamp, (int, float)):
            return None
        if not (0 <= (time.time() - timestamp) <= max_age_secs):
            logger.debug("Discarding stale daemon command '%s'", act)
            return None
        return act
    except (OSError, ValueError, TypeError) as exc:
        logger.debug("Failed to read daemon control command: %s", exc)
        return None
