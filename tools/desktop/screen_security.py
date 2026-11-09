"""
JARVIS OS — Phase 4 Screen Security, Privacy & Injection Shield
Sanitizes untrusted screen text, blocks indirect prompt injections,
enforces confirmation barriers on high-risk operations, and purges visual artifacts.
"""

import os
import re
import time
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("JARVIS.ScreenSecurity")

class ScreenSecurityGuard:
    """Enforces safety, privacy, and injection resistance across visual computer-use operations."""

    # Patterns indicating indirect prompt injection embedded in webpages or screenshots
    INJECTION_PATTERNS = [
        r"\bignore\s+(?:all\s+)?(?:previous|prior)\s+instructions\b",
        r"\breveal\s+(?:all\s+)?(?:passwords?|tokens?|keys?|secrets?)\b",
        r"\bsystem\s+override\b",
        r"\bdisregard\s+(?:safety|system)\s+rules\b",
        r"\bformat\s+(?:drive|disk|system)\b",
        r"\bexecute\s+as\s+root\b",
        r"\b(?:curl|wget)\s+https?://\S+\s*\|\s*(?:bash|sh)\b",
        r"\brm\s+-rf\s+[\/~]\b",
    ]

    # Operations requiring explicit interactive user confirmation
    SENSITIVE_ACTIONS = [
        "delete_file",
        "format_disk",
        "execute_elevated_command",
        "purchase",
        "payment",
        "submit_auth_form",
        "send_message",
        "publish_post",
        "robot_move",
        "robot_arm",
        "flash_firmware",
        "upload_credentials",
    ]

    def __init__(self):
        self._pending_confirmations: Dict[str, Dict[str, Any]] = {}

    def scan_untrusted_text(self, text: str) -> Dict[str, Any]:
        """Inspect visible page/document text for prompt injection signatures."""
        t_lower = text.lower()
        flagged = []
        for pat in self.INJECTION_PATTERNS:
            if re.search(pat, t_lower):
                flagged.append(pat)

        if flagged:
            logger.warning("Indirect prompt injection signature detected in screen text: %s", flagged)
            return {
                "safe": False,
                "threat_detected": True,
                "signatures": flagged,
                "sanitized_text": "[CONTENT ISOLATED: Potential Indirect Prompt Injection Detected]",
            }

        return {
            "safe": True,
            "threat_detected": False,
            "signatures": [],
            "sanitized_text": text,
        }

    def requires_confirmation(self, action_name: str, details: Optional[Dict[str, Any]] = None) -> bool:
        """Determine whether an action must be gated behind user confirmation."""
        act = action_name.lower()
        for sensitive in self.SENSITIVE_ACTIONS:
            if sensitive in act:
                return True

        if details:
            cmd = str(details.get("command", "")).lower()
            if "sudo" in cmd or "rm -rf" in cmd or "mkfs" in cmd or "dd if=" in cmd:
                return True

        return False

    def request_confirmation(self, action_name: str, target: str, description: str) -> Dict[str, Any]:
        """Register a gated action awaiting explicit user approval."""
        token = f"conf_{int(time.time())}_{os.urandom(4).hex()}"
        record = {
            "token": token,
            "action": action_name,
            "target": target,
            "description": description,
            "created_at": time.time(),
            "status": "PENDING_CONFIRMATION",
        }
        self._pending_confirmations[token] = record
        return record

    def confirm_action(self, token: str) -> bool:
        """Approve and release a gated action."""
        if token in self._pending_confirmations:
            self._pending_confirmations[token]["status"] = "CONFIRMED"
            return True
        return False


screen_security = ScreenSecurityGuard()
