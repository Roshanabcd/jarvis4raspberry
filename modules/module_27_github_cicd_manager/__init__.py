"""JARVIS OS Extension Module #27: GitHub & CI/CD Manager."""

from __future__ import annotations

from modules.module_27_github_cicd_manager.backend.app.main import create_app, mount_module

__version__ = "1.0.0"
__module_id__ = "module_27_github_cicd_manager"
__module_name__ = "GitHub & CI/CD Manager"

__all__ = ["create_app", "mount_module", "__version__", "__module_id__", "__module_name__"]
