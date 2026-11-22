"""JARVIS OS Extension Module #38: Plugin & Skills Marketplace."""

from __future__ import annotations

from modules.module_38_plugin_skills_marketplace.backend.app.main import create_app, mount_module

__version__ = "1.0.0"
__module_id__ = "module_38_plugin_skills_marketplace"
__module_name__ = "Plugin & Skills Marketplace"

__all__ = ["create_app", "mount_module", "__version__", "__module_id__", "__module_name__"]
