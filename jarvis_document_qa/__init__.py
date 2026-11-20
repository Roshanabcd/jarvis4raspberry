"""JARVIS OS — Document Question Answering package."""

from .config import DocumentQAConfig
from .router import create_router

__version__ = "1.0.0"
__all__ = ["DocumentQAConfig", "create_router", "__version__"]
