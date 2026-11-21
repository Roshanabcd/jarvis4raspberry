"""JARVIS OS Extension Module #37: Cross-Device Control Center."""

from __future__ import annotations

from modules.module_37_cross_device_control_center.backend.app.main import create_app, mount_module

__version__ = "1.0.0"
__module_id__ = "module_37_cross_device_control_center"
__module_name__ = "Cross-Device Control Center"

__all__ = ["create_app", "mount_module", "__version__", "__module_id__", "__module_name__"]
