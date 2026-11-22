"""JARVIS OS — AI Coding Assistant (Additive Feature Module #1).

Intelligent code generation, refactoring, security static analysis, and
automated test synthesis for JARVIS workspaces on Raspberry Pi 5.
"""

from .config import CodingAssistantConfig
from .router import create_router

__version__ = "1.0.0"
__all__ = ["CodingAssistantConfig", "create_router", "__version__"]
