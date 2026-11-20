"""JARVIS OS — AI Interview Bot (Additive Feature Module #3).

Interactive technical and behavioral interview simulation with dynamic
questioning, evaluation scoring, and structured feedback reports.
"""

from .config import InterviewBotConfig
from .router import create_router

__version__ = "1.0.0"
__all__ = ["InterviewBotConfig", "create_router", "__version__"]
