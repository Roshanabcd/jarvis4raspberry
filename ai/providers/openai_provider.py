"""OpenAI-compatible AI provider implementation."""

import logging
import os
from typing import Any, Dict, List, Optional
import requests
from ai.providers.base import AIProvider
from config.config_manager import config

logger = logging.getLogger("JARVIS-OPENAI")


class OpenAICompatibleProvider(AIProvider):
    """AIProvider implementation for OpenAI and OpenAI-compatible API services."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 30.0,
        enabled: Optional[bool] = None,
    ):
        """Initialize the OpenAI-compatible provider.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY environment variable).
            base_url: Base endpoint URL (default: https://api.openai.com/v1).
            model: Model name to use (default: gpt-4o).
            timeout: Request timeout in seconds.
            enabled: Explicit enabled flag. Defaults to config if omitted.
        """
        # Read from config if available
        models_cfg = config.get("providers", [])
        openai_cfg: Dict[str, Any] = {}
        for p in models_cfg:
            if isinstance(p, dict) and p.get("name") == "openai":
                openai_cfg = p
                break

        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "").strip()
        default_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.base_url = (base_url or openai_cfg.get("base_url") or default_base_url).rstrip("/")
        self.model = model or openai_cfg.get("model") or "gpt-4o"
        self.timeout = timeout

        if enabled is not None:
            self.enabled = enabled
        else:
            self.enabled = openai_cfg.get("enabled", False)

        logger.info(
            "OpenAICompatibleProvider initialized (model=%s, url=%s, enabled=%s, has_key=%s)",
            self.model,
            self.base_url,
            self.enabled,
            bool(self.api_key),
        )

    def is_available(self) -> bool:
        """Check if OpenAI provider is enabled and configured with an API key.

        Returns:
            True if enabled and key is present, False otherwise.
        """
        if not self.enabled:
            return False
        if not self.api_key:
            logger.debug("OpenAI API key missing; provider is not available.")
            return False
        return True

    def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        task_type: str = "general",
        **kwargs: Any,
    ) -> Optional[str]:
        """Generate a response using OpenAI Chat Completions API.

        Args:
            prompt: User prompt string.
            context: Optional context dictionary (e.g. system_prompt, history).
            task_type: Task type classification.
            **kwargs: Extra parameters passed to the API payload.

        Returns:
            Generated text string, or None if unavailable or on error.
        """
        if not self.enabled:
            logger.warning("OpenAICompatibleProvider is disabled.")
            return None

        if not self.api_key:
            logger.warning("OpenAICompatibleProvider called without an API key.")
            return None

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Build messages list
        messages: List[Dict[str, str]] = []
        if context and isinstance(context, dict):
            # If explicit message history provided, prepend it
            if "messages" in context and isinstance(context["messages"], list):
                messages.extend(context["messages"])
            else:
                sys_prompt = context.get("system_prompt") or context.get("system")
                if sys_prompt:
                    messages.append({"role": "system", "content": str(sys_prompt)})

        # Append current user prompt
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
        }

        # Copy any optional parameters
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]

        try:
            logger.debug("POSTing prompt to OpenAI completions endpoint: %s", url)
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                data = response.json()
                choices = data.get("choices", [])
                if choices and isinstance(choices, list):
                    first_choice = choices[0]
                    message = first_choice.get("message", {})
                    content = message.get("content", "")
                    return content
                logger.warning("OpenAI API response contained no choices: %s", data)
                return None
            else:
                logger.warning(
                    "OpenAI API returned HTTP %s: %s",
                    response.status_code,
                    response.text,
                )
                return None
        except requests.ConnectionError as ce:
            logger.warning("OpenAI connection error: %s", ce)
            return None
        except requests.Timeout as te:
            logger.warning("OpenAI request timed out after %s seconds: %s", self.timeout, te)
            return None
        except requests.RequestException as re:
            logger.warning("OpenAI request exception: %s", re)
            return None
        except Exception as exc:
            logger.error("Unexpected error in OpenAICompatibleProvider.generate: %s", exc, exc_info=True)
            return None

    def get_model_info(self) -> Dict[str, Any]:
        """Return provider configuration and model information.

        Returns:
            Dictionary containing model metadata.
        """
        return {
            "name": "openai",
            "model": self.model,
            "base_url": self.base_url,
            "enabled": self.enabled,
            "has_api_key": bool(self.api_key),
            "task_preference": ["vision", "code"],
        }


# Convenience alias
OpenAIProvider = OpenAICompatibleProvider
