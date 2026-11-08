"""Ollama AI provider implementation for local LLM inference on Raspberry Pi 5."""

import logging
from ai.providers.base import OllamaProvider

logger = logging.getLogger("JARVIS-OLLAMA")

__all__ = ["OllamaProvider"]
