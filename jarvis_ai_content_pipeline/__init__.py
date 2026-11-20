"""JARVIS OS — AI Content Creation Pipeline (Additive Feature Module #2).

End-to-end creative writing assistant for technical blogs, short-video scripts,
hooks, captions, and carousel outlines on Raspberry Pi 5.
"""

from .config import ContentPipelineConfig
from .router import create_router

__version__ = "1.0.0"
__all__ = ["ContentPipelineConfig", "create_router", "__version__"]
