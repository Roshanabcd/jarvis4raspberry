"""JARVIS OS — AI Social Media Automation (Additive Feature Module #4).

Multi-platform content planning, automated copy generation, scheduled
publishing workflows, and engagement analytics for Raspberry Pi 5.
"""

from .config import SocialAutomationConfig
from .router import create_router

__version__ = "1.0.0"
__all__ = ["SocialAutomationConfig", "create_router", "__version__"]
