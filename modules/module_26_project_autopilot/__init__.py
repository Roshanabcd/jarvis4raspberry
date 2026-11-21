"""JARVIS OS Extension Module #26: Project Autopilot."""

from __future__ import annotations

from modules.module_26_project_autopilot.backend.app.main import create_app, mount_module

__version__ = "1.0.0"
__module_id__ = "module_26_project_autopilot"
__module_name__ = "Project Autopilot"

__all__ = ["create_app", "mount_module", "__version__", "__module_id__", "__module_name__"]
