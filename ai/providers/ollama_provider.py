"""Ollama AI provider implementation for local LLM inference."""

import logging
from typing import Any, Dict, Optional
import requests
from ai.providers.base import AIProvider
from config.config_manager import config

logger = logging.getLogger("JARVIS-OLLAMA")


class OllamaProvider(AIProvider):
    """AIProvider implementation for locally hosted Ollama instances."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 30.0,
        enabled: bool = True,
    ):
        """Initialize the Ollama provider.

        Args:
            base_url: Base URL for Ollama API (default: http://localhost:11434).
            model: Model identifier (default: llama3.2).
            timeout: Request timeout in seconds.
            enabled: Whether this provider is enabled.
        """
        # Read defaults from models config if available
        models_cfg = config.get("providers", [])
        ollama_cfg: Dict[str, Any] = {}
        for p in models_cfg:
            if isinstance(p, dict) and p.get("name") == "ollama":
                ollama_cfg = p
                break

        self.base_url = (base_url or ollama_cfg.get("base_url") or "http://localhost:11434").rstrip("/")
        self.model = model or ollama_cfg.get("model") or "llama3.2"
        self.timeout = timeout
        self.enabled = enabled if enabled is not None else ollama_cfg.get("enabled", True)
        self.simulation_mode = config.get("simulation_mode", True)

        logger.info(
            "OllamaProvider initialized (model=%s, url=%s, enabled=%s, sim=%s)",
            self.model,
            self.base_url,
            self.enabled,
            self.simulation_mode,
        )

    def is_available(self) -> bool:
        """Check if the Ollama service is reachable and responding.

        Returns:
            True if available and responding with HTTP 200, False otherwise.
        """
        if not self.enabled:
            return False

        url = f"{self.base_url}/api/tags"
        try:
            response = requests.get(url, timeout=2.0)
            return response.status_code == 200
        except (requests.RequestException, Exception) as exc:
            logger.debug("Ollama availability check failed: %s", exc)
            return False

    def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        task_type: str = "general",
        **kwargs: Any,
    ) -> Optional[str]:
        """Generate text using Ollama /api/generate endpoint.

        Args:
            prompt: Prompt text to complete.
            context: Optional context dictionary (e.g. system prompt, template variables).
            task_type: Task type classification.
            **kwargs: Extra parameters passed directly to the Ollama payload.

        Returns:
            Response text if successful, or None if unavailable or on error.
        """
        if not self.enabled:
            logger.warning("Ollama provider is disabled.")
            return None

        url = f"{self.base_url}/api/generate"
        payload: Dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "prompt": prompt,
            "stream": False,
        }

        # Incorporate system prompt if provided in context
        if context and isinstance(context, dict):
            if "system_prompt" in context:
                payload["system"] = context["system_prompt"]
            elif "system" in context:
                payload["system"] = context["system"]

        # Incorporate any extra options
        if "options" in kwargs:
            payload["options"] = kwargs["options"]

        try:
            logger.debug("POSTing prompt to Ollama endpoint: %s", url)
            response = requests.post(url, json=payload, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                logger.warning(
                    "Ollama API returned HTTP %s: %s",
                    response.status_code,
                    response.text,
                )
                return None
        except requests.ConnectionError as ce:
            logger.warning("Ollama connection error (service unreachable): %s", ce)
            return None
        except requests.Timeout as te:
            logger.warning("Ollama request timed out after %s seconds: %s", self.timeout, te)
            return None
        except requests.RequestException as re:
            logger.warning("Ollama request exception: %s", re)
            return None
        except Exception as exc:
            logger.error("Unexpected error in OllamaProvider.generate: %s", exc, exc_info=True)
            return None

    def get_model_info(self) -> Dict[str, Any]:
        """Return provider configuration and model information.

        Returns:
            Dictionary containing model metadata.
        """
        return {
            "name": "ollama",
            "model": self.model,
            "base_url": self.base_url,
            "enabled": self.enabled,
            "task_preference": ["simple", "general"],
        }
