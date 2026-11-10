"""
JARVIS OS — Apps Center Permission and Role Governance.
Enforces multi-tiered RBAC (ADMIN, USER, GUEST) across Apps Center APIs,
preventing privilege escalation and unauthorized application launches.
"""

import logging
from typing import Optional, Tuple

from tools.identity.permission_manager import permission_manager
from tools.identity.user_manager import UserRole, user_manager
from apps.apps_center.models import ApplicationManifest, AppStatus
from apps.apps_center.registry import app_registry

logger = logging.getLogger("JARVIS.AppsCenter.Permissions")

ROLE_HIERARCHY = {
    UserRole.GUEST.value: 1,
    UserRole.USER.value: 2,
    UserRole.ADMIN.value: 3,
}


class AppsPermissionEngine:
    """Enforces application-level access control on the backend."""

    @staticmethod
    def get_current_user_role(pin: Optional[str] = None, user_id: Optional[str] = None) -> Tuple[str, str]:
        """
        Derive active user ID and verified role from session, PIN, or active face.
        Defaults to ('guest', 'GUEST') for safety.
        """
        # If valid admin PIN is provided, verify against UserManager
        if pin:
            is_valid, msg = user_manager.verify_admin_pin(pin)
            if is_valid:
                admin_user = user_manager.get_admin_user()
                admin_name = admin_user.get("username", "admin") if admin_user else "admin"
                return admin_name, UserRole.ADMIN.value

        # Check if user_id is an enrolled user in UserManager
        if user_id and user_id.lower() != "guest":
            for u in user_manager.list_users():
                if u.get("username") == user_id:
                    return user_id, u.get("role", UserRole.USER.value)
            # Default non-guest usernames to standard USER role
            return user_id, UserRole.USER.value

        # Safe default
        return "guest", UserRole.GUEST.value

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
