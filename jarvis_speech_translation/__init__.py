"""JARVIS OS — Real-Time Speech Translation package."""

from .config import SpeechTranslationConfig
from .router import create_router

__version__ = "1.0.0"
__all__ = ["SpeechTranslationConfig", "create_router", "__version__"]
