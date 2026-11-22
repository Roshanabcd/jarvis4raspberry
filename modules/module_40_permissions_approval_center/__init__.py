"""JARVIS OS Extension Module #40: Permissions & Approval Center."""

from __future__ import annotations

from modules.module_40_permissions_approval_center.backend.app.main import create_app, mount_module

__version__ = "1.0.0"
__module_id__ = "module_40_permissions_approval_center"
__module_name__ = "Permissions & Approval Center"

__all__ = ["create_app", "mount_module", "__version__", "__module_id__", "__module_name__"]
