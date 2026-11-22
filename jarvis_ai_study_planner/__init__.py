"""JARVIS OS — AI Study Planner (Additive Feature Module #5).

Personalized study scheduling, learning goal breakdown, SM-2 spaced-repetition
tracking, and syllabus milestone management for Raspberry Pi 5.
"""

from .config import StudyPlannerConfig
from .router import create_router

__version__ = "1.0.0"
__all__ = ["StudyPlannerConfig", "create_router", "__version__"]
