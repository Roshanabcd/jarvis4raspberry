"""JARVIS OS — Handwritten to Text Converter package."""

from .config import HandwritingOCRConfig
from .router import create_router

__version__ = "1.0.0"
__all__ = ["HandwritingOCRConfig", "create_router", "__version__"]
