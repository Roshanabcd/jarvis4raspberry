"""OpenAI-compatible AI provider implementation."""

import logging
from ai.providers.base import OpenAIProvider, OpenAICompatibleProvider

logger = logging.getLogger("JARVIS-OPENAI")

__all__ = ["OpenAIProvider", "OpenAICompatibleProvider"]
