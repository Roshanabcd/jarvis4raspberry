"""JARVIS OS Extension Module #22: Intelligent AI Model Router."""

from __future__ import annotations

from modules.module_22_intelligent_model_router.backend.app.main import create_app, mount_module

__version__ = "1.0.0"
__module_id__ = "module_22_intelligent_model_router"
__module_name__ = "Intelligent AI Model Router"

__all__ = ["create_app", "mount_module", "__version__", "__module_id__", "__module_name__"]
