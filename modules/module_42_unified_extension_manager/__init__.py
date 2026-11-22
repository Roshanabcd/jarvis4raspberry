"""JARVIS OS Extension Module #42: Unified Extension Manager & SDK."""

from __future__ import annotations

from modules.module_42_unified_extension_manager.backend.app.main import create_app, mount_module

__version__ = "1.0.0"
__module_id__ = "module_42_unified_extension_manager"
__module_name__ = "Unified Extension Manager & SDK"

__all__ = ["create_app", "mount_module", "__version__", "__module_id__", "__module_name__"]
