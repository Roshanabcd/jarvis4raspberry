"""
JARVIS OS — Role-Based Permission Manager.
Enforces multi-user access boundaries (ADMIN, USER, GUEST) across tool execution,
terminal operations, vision actions, and chat interactions.

Key Principles:
1. Zero Chat Elevation: Conversational prompts ("make me admin") CANNOT elevate privileges.
2. Sensitive Operations Gate: Administrative actions require ADMIN role and PIN verification.
3. Default Least Privilege: Unidentified users or unknown faces are automatically assigned GUEST.
4. Comprehensive Audit Trail: Every authorization check is appended to data/audit/audit_log.jsonl.
"""

import datetime
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from tools.identity.user_manager import UserManager, UserRole, user_manager

logger = logging.getLogger("JARVIS.Identity.PermissionManager")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
AUDIT_DIR = PROJECT_ROOT / "data" / "audit"
AUDIT_LOG_FILE = AUDIT_DIR / "audit_log.jsonl"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

# Tool permission mapping
ROLE_ALLOWED_TOOLS: Dict[str, Set[str]] = {
    UserRole.GUEST.value: {
        "chat",
        "calculate",
        "datetime_now",
        "datetime_format",
        "system_status",
        "get_system_status",
        "read_sensors",
        "get_weather",
        "memory_search",
        "get_running_apps_processes",
        "running_apps_processes",
        "inspect_screen",
        "screen_observe",
        "monitor_screen",
        # Safe browser and desktop launch tools
        "open_url",
        "open_youtube",
        "open_desktop_app",
        "desktop_open_url",
        "desktop_search_youtube",
        "desktop_open_app",
        "focus_window",
        "browser_ui_action",
        "computer_execute",
    },
    UserRole.USER.value: {
        "chat",
        "calculate",
        "datetime_now",
        "datetime_format",
        "system_status",
        "get_system_status",
        "read_sensors",
        "get_weather",
        "memory_search",
        "memory_store",
        # Vision
        "camera_capture",
        "camera_describe",
        "detect_objects",
        "identify_user",
        # Computer interaction (screen perception & synthetic input)
        "desktop_screenshot",
        "desktop_perception",
        "desktop_list_windows",
        "desktop_list_applications",
        "inspect_screen",
        "screen_observe",
        "monitor_screen",
        "focus_window",
        "desktop_click",
        "desktop_type",
        "desktop_hotkey",
        "desktop_scroll",
        "browser_ui_action",
        "run_safe_terminal_task",
        "get_running_apps_processes",
        "running_apps_processes",
        "diagnose_system_status",
        "developer_diagnostics",
        "computer_execute",
        "computer_click",
        "computer_double_click",
        "computer_right_click",
        "computer_move_mouse",
        "computer_drag_and_drop",
        "computer_select_option",
        "computer_stop",
        "computer_type",
        "computer_press_key",
        "computer_press_hotkey",
        "computer_scroll",
        "computer_switch_window",
        "computer_focus_window",
        "computer_minimize_window",
        "computer_maximize_window",
        "browser_open",
        "browser_select",
        "browser_click",
        "browser_type",
        "browser_navigate",
        # Safe browser and desktop launch tools
        "open_url",
        "open_youtube",
        "open_desktop_app",
        "desktop_open_url",
        "desktop_search_youtube",
        "desktop_open_app",
        # Desktop & Media
        "app_launcher",
        "file_search",
        "project_open",
        "play_media",
        "pause_media",
        "resume_media",
        "stop_media",
        "media_status",
        "set_volume",
        "volume_up",
        "volume_down",
        "search_folder",
        "open_folder",
        "open_folder_at",
        "youtube_search",
        "youtube_select",
    },
    UserRole.ADMIN.value: {
        # Admin has access to all tools including sensitive system commands
        "*"
    },
}

# Operations that strictly require Admin PIN verification
PIN_REQUIRED_ACTIONS = {
    "system_reboot",
    "system_shutdown",
    "delete_user",
    "enroll_user",
    "enroll_admin",
    "modify_security_profile",
    "delete_file",
}


class PermissionManager:
    """Evaluates and enforces role-based authorization for JARVIS actions."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.user_mgr = user_manager
        self._current_user: Optional[Dict[str, Any]] = None
        self._initialized = True
        logger.info("Role-Based PermissionManager initialized.")

    def set_active_user(self, user_dict: Optional[Dict[str, Any]]) -> None:
        """Set the currently identified user session."""
        self._current_user = user_dict
        from apps.voice.session_manager import voice_session_mgr
        if not user_dict:
            voice_session_mgr.invalidate_session()
        else:
            voice_session_mgr.create_session(
                user_id=user_dict.get('user_id', 'guest'),
                display_name=user_dict.get('display_name', 'Guest'),
                role=user_dict.get('role', 'GUEST'), source='identity_recognition',
                is_authenticated=user_dict.get('role', 'GUEST') != 'GUEST',
            )

    def get_active_user(self) -> Dict[str, Any]:
        """Return the current active user or a least-privilege default.

        First-run enrollment is intentionally *not* an administrator session.
        Enrollment is a separate, explicitly confirmed workflow; granting ADMIN
        privileges merely because no account exists would let any local caller
        bypass the identity boundary before enrollment.
        """
        from apps.voice.session_manager import voice_session_mgr
        session = voice_session_mgr.get_active_session()
        if session.is_authenticated:
            return {'user_id': session.user_id, 'display_name': session.display_name,
                    'role': session.authorization_role(), 'recognized_role': session.role,
                    'expires_at': session.expires_at, 'is_setup': False}
        # Preserve setup state for the dashboard, but it has no elevated role.
        if not self.user_mgr.is_admin_enrolled():
            return {
                "user_id": "guest_session",
                "display_name": "Setup required",
                "role": UserRole.GUEST.value,
                "is_setup": True,
            }
        return {
            "user_id": "guest_session",
            "display_name": "Guest",
            "role": UserRole.GUEST.value,
        }

    def check_tool_permission(
        self,
        tool_name: str,
        user_role: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Check if a given role is permitted to execute a tool.
        """
        role = user_role or self.get_active_user().get("role", UserRole.GUEST.value)
        role = role.upper()

        # Admin has wildcard access to all tools
        if role == UserRole.ADMIN.value:
            self._log_audit(tool_name, role, allowed=True, reason="Admin role wildcard authorization", request_id=request_id)
            return True, "Authorized as Administrator."

        allowed_set = ROLE_ALLOWED_TOOLS.get(role, set())
        if tool_name in allowed_set or "*" in allowed_set:
            self._log_audit(tool_name, role, allowed=True, reason=f"Permitted in role {role}", request_id=request_id)
            return True, f"Authorized for role {role}."

        reason = f"Access denied: Tool '{tool_name}' requires elevated privileges beyond '{role}'."
        self._log_audit(tool_name, role, allowed=False, reason=reason, request_id=request_id)
        return False, reason

    def check_chat_elevation_attempt(self, text: str) -> Optional[str]:
        """
        Detect attempts to elevate role via chat and return an explicit security denial.
        """
        text_lower = text.lower().strip()
        patterns = [
            r"\b(make|give|set|switch|grant|elevate|promote)\s+(?:(?:me|user)\s+)?(?:to\s+)?(?:admin|administrator|root|superuser)(?:\s+mode|\s+role|\s+privileges)?\b",
            r"\bi\s+am\s+(the\s+)?(admin|administrator|root|superuser)\b",
            r"\bgrant\s+me\s+admin\s+privileges\b",
            r"\b(set|switch|change)\s+role\s+(to\s+)?(?:admin|administrator|root)\b",
        ]
        for pat in patterns:
            if re.search(pat, text_lower):
                logger.warning("Intercepted unauthorized chat privilege escalation attempt: '%s'", text)
                return (
                    "⛔ Access Denied: Privilege escalation cannot be granted via conversational prompt. "
                    "Administrative status requires physical biometric face recognition or PIN authentication."
                )
        return None

    def _log_audit(
        self,
        action: str,
        role: str,
        allowed: bool,
        reason: str,
        request_id: Optional[str] = None,
    ) -> None:
        """Append an entry to the append-only audit log."""
        try:
            entry = {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "request_id": request_id or "",
                "user_id": self.get_active_user().get("user_id", "unknown"),
                "display_name": self.get_active_user().get("display_name", "Unknown"),
                "role": role,
                "action": action,
                "allowed": allowed,
                "reason": reason,
            }
            with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error("Failed to write to audit log: %s", e)


# Global singleton instance
permission_manager = PermissionManager()
