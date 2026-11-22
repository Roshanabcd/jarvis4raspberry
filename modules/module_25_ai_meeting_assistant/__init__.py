"""JARVIS OS Extension Module #25: AI Meeting Assistant."""

from __future__ import annotations

from modules.module_25_ai_meeting_assistant.backend.app.main import create_app, mount_module

__version__ = "1.0.0"
__module_id__ = "module_25_ai_meeting_assistant"
__module_name__ = "AI Meeting Assistant"

__all__ = ["create_app", "mount_module", "__version__", "__module_id__", "__module_name__"]
