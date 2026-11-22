"""JARVIS OS Extension Module #32: System Health & Diagnostics."""

from __future__ import annotations

from modules.module_32_system_health_diagnostics.backend.app.main import create_app, mount_module

__version__ = "1.0.0"
__module_id__ = "module_32_system_health_diagnostics"
__module_name__ = "System Health & Diagnostics"

__all__ = ["create_app", "mount_module", "__version__", "__module_id__", "__module_name__"]
