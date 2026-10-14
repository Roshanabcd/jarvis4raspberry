"""Model router for selecting the optimal AI provider based on task and environment."""

import logging
import socket
from typing import Any, Dict, List, Optional
from ai.providers.base import AIProvider
from ai.providers.ollama_provider import OllamaProvider
from ai.providers.openai_provider import OpenAICompatibleProvider
from config.config_manager import config

logger = logging.getLogger("JARVIS-ROUTER")

# Task type routing preferences
TASK_PREFERENCES: Dict[str, List[str]] = {
    "simple": ["ollama", "openai"],
    "code": ["openai", "ollama"],
    "vision": ["openai", "ollama"],
    "general": ["ollama", "openai"],
}


class ModelRouter:
    """Intelligent router that directs queries to local or cloud AI providers."""

    def __init__(
        self,
        providers: Optional[Dict[str, AIProvider]] = None,
        fallback_message: Optional[str] = None,
    ):
        """Initialize ModelRouter and load providers.

        Args:
            providers: Optional explicit dictionary of provider instances.
            fallback_message: Message to return if all providers are unavailable.
        """
        self.fallback_message = fallback_message or config.get(
            "fallback_message",
            "I am operating in offline mode. Cloud AI is unavailable.",
        )
        self.default_provider_name = config.get("default_provider", "ollama")
        self.simulation_mode = config.get("simulation_mode", True)

        if providers is not None:
            self.providers = providers
        else:
            self.providers = self._load_providers()

        logger.info(
            "ModelRouter initialized with %d providers: %s (default=%s)",
            len(self.providers),
            list(self.providers.keys()),
            self.default_provider_name,
        )

    def _load_providers(self) -> Dict[str, AIProvider]:
        """Instantiate configured providers."""
        loaded: Dict[str, AIProvider] = {}
        try:
            loaded["ollama"] = OllamaProvider()
        except Exception as exc:
            logger.warning("Failed to initialize OllamaProvider: %s", exc)

        try:
            loaded["openai"] = OpenAICompatibleProvider()
        except Exception as exc:
            logger.warning("Failed to initialize OpenAICompatibleProvider: %s", exc)

        return loaded

    def check_internet_connectivity(self, host: str = "8.8.8.8", port: int = 53, timeout: float = 1.0) -> bool:
        """Check if an external internet connection is currently reachable.

        Args:
            host: Public DNS or gateway IP address.
            port: Port to test (default: DNS port 53).
            timeout: Timeout duration in seconds.

        Returns:
            True if connection succeeds, False otherwise.
        """
        try:
            socket.setdefaulttimeout(timeout)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((host, port))
            return True
        except (socket.timeout, socket.error, OSError):
            return False

    def get_status(self) -> Dict[str, Any]:
        """Return status and availability information for all providers.

        Returns:
            Dictionary mapping provider names and connectivity to status booleans.
        """
        is_online = self.check_internet_connectivity()
        status: Dict[str, Any] = {
            "internet_connected": is_online,
            "default_provider": self.default_provider_name,
        }

        provider_availability: Dict[str, bool] = {}
        for name, provider in self.providers.items():
            # If cloud-based (e.g. openai) and offline, mark unavailable
            if name == "openai" and not is_online:
                provider_availability[name] = False
            else:
                try:
                    provider_availability[name] = provider.is_available()
                except Exception as exc:
                    logger.debug("Error checking status for provider %s: %s", name, exc)
                    provider_availability[name] = False

        status.update(provider_availability)
        status["providers"] = provider_availability
        return status

    def route(
        self,
        prompt: str,
        task_type: str = "general",
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        """Route the prompt to the best available provider based on task type.

        Selection preferences:
            - 'simple': prefers ollama, then openai
            - 'code': prefers openai, then ollama
            - 'vision': prefers openai, then ollama
            - 'general': tries ollama first, then openai

        Args:
            prompt: Text prompt to submit.
            task_type: Classification string ('vision', 'code', 'simple', 'general').
            context: Optional context dictionary.
            **kwargs: Extra parameters passed to the provider.

        Returns:
            Generated response string or fallback message if all providers fail.
        """
        task_key = task_type.lower().strip() if task_type else "general"
        candidate_order = TASK_PREFERENCES.get(task_key, TASK_PREFERENCES["general"])

        is_online = self.check_internet_connectivity()
        logger.debug(
            "Routing task '%s' (internet=%s, order=%s)",
            task_key,
            is_online,
            candidate_order,
        )

        for provider_name in candidate_order:
            provider = self.providers.get(provider_name)
            if not provider:
                continue

            # Cloud provider check: skip OpenAI if internet is unavailable
            if provider_name == "openai" and not is_online:
                logger.debug("Skipping cloud provider '%s' due to lack of internet connection", provider_name)
                continue

            try:
                if not provider.is_available():
                    logger.debug("Provider '%s' is currently not available.", provider_name)
                    continue

                logger.info("Attempting generation using provider '%s' for task '%s'", provider_name, task_key)
                response = provider.generate(prompt, context=context, task_type=task_key, **kwargs)
                if response is not None and response.strip():
                    return response
                logger.warning("Provider '%s' returned empty or None response.", provider_name)
            except Exception as exc:
                logger.warning("Error running provider '%s': %s", provider_name, exc)

        logger.warning("All providers failed or were unavailable. Falling back to offline message.")
        return self.fallback_message
