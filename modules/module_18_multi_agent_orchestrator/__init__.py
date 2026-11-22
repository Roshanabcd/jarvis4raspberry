"""JARVIS OS Extension Module #18: Multi-Agent Task Orchestrator."""

from __future__ import annotations

from modules.module_18_multi_agent_orchestrator.backend.app.main import create_app, mount_module

__version__ = "1.0.0"
__module_id__ = "module_18_multi_agent_orchestrator"
__module_name__ = "Multi-Agent Task Orchestrator"

__all__ = ["create_app", "mount_module", "__version__", "__module_id__", "__module_name__"]
