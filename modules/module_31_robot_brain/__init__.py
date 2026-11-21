"""JARVIS OS Extension Module #31: JARVIS Robot Brain."""

from __future__ import annotations

from modules.module_31_robot_brain.backend.app.main import create_app, mount_module

__version__ = "1.0.0"
__module_id__ = "module_31_robot_brain"
__module_name__ = "JARVIS Robot Brain"

__all__ = ["create_app", "mount_module", "__version__", "__module_id__", "__module_name__"]
