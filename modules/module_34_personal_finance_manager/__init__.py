"""JARVIS OS Extension Module #34: Personal Finance Manager."""

from __future__ import annotations

from modules.module_34_personal_finance_manager.backend.app.main import create_app, mount_module

__version__ = "1.0.0"
__module_id__ = "module_34_personal_finance_manager"
__module_name__ = "Personal Finance Manager"

__all__ = ["create_app", "mount_module", "__version__", "__module_id__", "__module_name__"]
