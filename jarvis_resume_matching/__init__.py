"""JARVIS OS — Smart Resume Matching package."""

from .config import ResumeMatchingConfig
from .router import create_router

__version__ = "1.0.0"
__all__ = ["ResumeMatchingConfig", "create_router", "__version__"]
