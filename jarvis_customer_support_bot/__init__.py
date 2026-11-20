"""JARVIS OS — ChatGPT-Powered Customer Support Bot (Additive Feature Module #8).

Domain-specific customer inquiry answering, ticket triage, sentiment
classification, and escalation routing for Raspberry Pi 5.
"""

from .config import SupportBotConfig
from .router import create_router

__version__ = "1.0.0"
__all__ = ["SupportBotConfig", "create_router", "__version__"]
