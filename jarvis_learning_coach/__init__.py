"""JARVIS OS — Personalized Learning AI Coach package."""

from .config import LearningCoachConfig
from .router import create_router

__version__ = "1.0.0"
__all__ = ["LearningCoachConfig", "create_router", "__version__"]
