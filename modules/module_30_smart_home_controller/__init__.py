"""JARVIS OS Extension Module #30: Smart Home Controller."""

from __future__ import annotations

from modules.module_30_smart_home_controller.backend.app.main import create_app, mount_module

__version__ = "1.0.0"
__module_id__ = "module_30_smart_home_controller"
__module_name__ = "Smart Home Controller"

__all__ = ["create_app", "mount_module", "__version__", "__module_id__", "__module_name__"]
