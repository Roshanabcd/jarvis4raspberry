"""JARVIS OS Extension Module #21: Intelligent Browser Agent."""

from __future__ import annotations

from modules.module_21_intelligent_browser_agent.backend.app.main import create_app, mount_module

__version__ = "1.0.0"
__module_id__ = "module_21_intelligent_browser_agent"
__module_name__ = "Intelligent Browser Agent"

__all__ = ["create_app", "mount_module", "__version__", "__module_id__", "__module_name__"]
