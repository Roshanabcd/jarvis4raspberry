"""JARVIS OS Extension Module #24: Email & Calendar Assistant."""

from __future__ import annotations

from modules.module_24_email_calendar_assistant.backend.app.main import create_app, mount_module

__version__ = "1.0.0"
__module_id__ = "module_24_email_calendar_assistant"
__module_name__ = "Email & Calendar Assistant"

__all__ = ["create_app", "mount_module", "__version__", "__module_id__", "__module_name__"]
