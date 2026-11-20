"""
JARVIS OS — Apps Center Permission and Role Governance.
Enforces multi-tiered RBAC (ADMIN, USER, GUEST) across Apps Center APIs,
preventing privilege escalation and unauthorized application launches.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Tuple

from tools.identity.permission_manager import permission_manager
from tools.identity.user_manager import UserRole
from apps.apps_center.models import ApplicationManifest, AppStatus

logger = logging.getLogger("JARVIS.AppsCenter.Permissions")

ROLE_HIERARCHY = {
    UserRole.GUEST.value: 1,
    UserRole.USER.value: 2,
    UserRole.ADMIN.value: 3,
}


@dataclass(frozen=True)
class AppRequestIdentity:
    """A normalized, server-owned identity for Apps Center requests.

    The current identity subsystem is process-local and therefore suitable only
    for a single local operator.  It is deliberately resolved on the server,
    rather than from request-supplied ``user_id`` or role values.
    """

    user_id: str
    display_name: str
    role: str
    is_setup: bool = False


class AppsPermissionEngine:
    """Enforces application-level access control on the backend."""

    @staticmethod
    def get_current_identity() -> AppRequestIdentity:
        """
        Resolve a request identity from the server-owned active identity.

        Browser input is never accepted as identity evidence.  A malformed or
        incomplete identity falls back to the same GUEST state used elsewhere
        in the system.
        """
        active = permission_manager.get_active_user() or {}
        role = str(active.get("role", UserRole.GUEST.value)).upper()
        if role not in ROLE_HIERARCHY:
            role = UserRole.GUEST.value

        user_id = str(active.get("user_id") or "guest_session").strip()
        if not user_id:
            user_id = "guest_session"

        display_name = str(active.get("display_name") or "Guest").strip() or "Guest"
        return AppRequestIdentity(
            user_id=user_id,
            display_name=display_name,
            role=role,
            is_setup=bool(active.get("is_setup", False)),
        )

    @classmethod
    def get_current_user_role(cls) -> Tuple[str, str]:
        """Compatibility helper returning the server-owned user ID and role."""
        identity = cls.get_current_identity()
        return identity.user_id, identity.role

    @classmethod
    def can_access_app(cls, app: ApplicationManifest, role: str) -> Tuple[bool, Optional[str]]:
        """
        Check if user with `role` can view or interact with `app`.
        """
        user_level = ROLE_HIERARCHY.get(role.upper(), 1)
        req_level = ROLE_HIERARCHY.get(app.minimum_role.upper(), 2)

        if user_level < req_level:
            return False, f"Access requires {app.minimum_role} role. Current role is {role}."

        if app.status == AppStatus.DISABLED:
            return False, f"Application '{app.name}' has been disabled by administrator."

        return True, None

    @classmethod
    def can_launch_app(cls, app: ApplicationManifest, role: str) -> Tuple[bool, Optional[str]]:
        """
        Check if user can launch `app`.
        Enforces that PLANNED applications cannot be launched.
        """
        can_access, reason = cls.can_access_app(app, role)
        if not can_access:
            return False, reason

        if app.status == AppStatus.PLANNED:
            return False, f"Application '{app.name}' is currently in roadmap (Planned) and cannot be launched."

        if app.status != AppStatus.AVAILABLE:
            return False, f"Application '{app.name}' is not in Available state (current status: {app.status.value})."

        return True, None

    @classmethod
    def can_manage_settings(cls, role: str) -> bool:
        """Only ADMIN users can configure global app settings or toggle providers."""
        return role.upper() == UserRole.ADMIN.value


# Global singleton
apps_permissions = AppsPermissionEngine()
