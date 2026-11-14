"""Simulated local AI provider for testing and fallback."""

from typing import Any, Dict, List, Optional, Union

from ai.providers.base import AIProvider


class SimulatedLocalProvider(AIProvider):
    """Simulation AI provider that returns predictable responses."""

    name = "simulated"
    enabled = True

    def __init__(self, model_name: str = "simulated-local", enabled: bool = True):
        self.model = model_name
        self.model_name = model_name
        self.enabled = enabled

    def generate(
        self,
        messages: Union[List[Dict], str],
        tools: Optional[List[Dict]] = None,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        if isinstance(messages, str):
            prompt = messages
        else:
            prompt = ""
            for item in reversed(messages):
                if item.get("role") == "user":
                    prompt = str(item.get("content", ""))
                    break
        text = f"Simulated response to: {prompt[:50]}..."
        if isinstance(messages, str):
            return text
        return {
            "text": text,
            "tool_calls": [],
            "provider": self.name,
            "model": self.model,
            "tokens": 0,
        }

    def is_available(self) -> bool:
        return bool(self.enabled)

    def list_models(self) -> List[str]:
        return [self.model]

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "model": self.model,
            "enabled": self.enabled,
            "type": "local_sim",
            "simulated": True,
            "task_preference": ["testing", "fallback"],
        }
