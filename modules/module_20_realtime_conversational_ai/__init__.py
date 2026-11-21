"""JARVIS OS Extension Module #20: Real-Time Conversational AI."""

from __future__ import annotations

from modules.module_20_realtime_conversational_ai.backend.app.main import create_app, mount_module

__version__ = "1.0.0"
__module_id__ = "module_20_realtime_conversational_ai"
__module_name__ = "Real-Time Conversational AI"

__all__ = ["create_app", "mount_module", "__version__", "__module_id__", "__module_name__"]
