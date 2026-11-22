"""JARVIS OS — End-to-End AI Search Engine package."""

from .config import AISearchConfig
from .router import create_router

__version__ = "1.0.0"
__all__ = ["AISearchConfig", "create_router", "__version__"]
