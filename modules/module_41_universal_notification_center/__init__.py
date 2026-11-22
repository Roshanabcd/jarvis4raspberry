"""JARVIS OS Extension Module #41: Universal Notification Center."""

from __future__ import annotations

from modules.module_41_universal_notification_center.backend.app.main import create_app, mount_module

__version__ = "1.0.0"
__module_id__ = "module_41_universal_notification_center"
__module_name__ = "Universal Notification Center"

__all__ = ["create_app", "mount_module", "__version__", "__module_id__", "__module_name__"]
