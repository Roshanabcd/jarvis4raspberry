"""JARVIS OS Extension Module #19: Autonomous Computer Assistant."""

from __future__ import annotations

from modules.module_19_autonomous_computer_assistant.backend.app.main import create_app, mount_module

__version__ = "1.0.0"
__module_id__ = "module_19_autonomous_computer_assistant"
__module_name__ = "Autonomous Computer Assistant"

__all__ = ["create_app", "mount_module", "__version__", "__module_id__", "__module_name__"]
