"""JARVIS OS Extension Module #28: AI Data Analyst."""

from __future__ import annotations

from modules.module_28_ai_data_analyst.backend.app.main import create_app, mount_module

__version__ = "1.0.0"
__module_id__ = "module_28_ai_data_analyst"
__module_name__ = "AI Data Analyst"

__all__ = ["create_app", "mount_module", "__version__", "__module_id__", "__module_name__"]
