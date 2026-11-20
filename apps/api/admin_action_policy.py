"""Fresh administrator authorization for privileged local API actions.

Configuration writes, backup export, and diagnostic commands can expose secrets,
change safety policy, or operate attached devices.  They therefore require an
explicit acknowledgement and a newly supplied administrator PIN on every
request.  This is intentionally separate from a browser's display state.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Header, HTTPException

from tools.identity.user_manager import user_manager


ADMIN_ACTION_CONFIRMATION_VALUE = "privileged-settings-action"


def require_admin_action(
    x_jarvis_admin_pin: Optional[str] = Header(default=None),
    x_jarvis_admin_confirmation: Optional[str] = Header(default=None),
) -> None:
    """Require a fresh PIN and deliberate acknowledgement for privileged work."""
    if x_jarvis_admin_confirmation != ADMIN_ACTION_CONFIRMATION_VALUE:
        raise HTTPException(
            status_code=428,
            detail="Explicit privileged-settings-action confirmation is required.",
        )
    if not x_jarvis_admin_pin:
        raise HTTPException(status_code=401, detail="Fresh administrator PIN is required.")

    valid, message = user_manager.verify_admin_pin(x_jarvis_admin_pin)
    if not valid:
        raise HTTPException(status_code=401, detail=f"Administrator verification failed: {message}")

