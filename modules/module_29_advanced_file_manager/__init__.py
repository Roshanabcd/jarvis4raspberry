"""JARVIS OS Extension Module #29: Advanced File Manager."""

from __future__ import annotations

from modules.module_29_advanced_file_manager.backend.app.main import create_app, mount_module

__version__ = "1.0.0"
__module_id__ = "module_29_advanced_file_manager"
__module_name__ = "Advanced File Manager"

__all__ = ["create_app", "mount_module", "__version__", "__module_id__", "__module_name__"]
