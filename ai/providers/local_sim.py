"""Simulated local AI provider for testing and fallback."""

from typing import Any, Dict, Optional
from ai.providers.base import AIProvider


class SimulatedLocalProvider(AIProvider):
    """Simulation AI provider that returns predictable responses."""

    def __init__(self, model_name: str = "simulated-local"):
        self.model_name = model_name

    def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        task_type: str = "general",
        **kwargs: Any,
    ) -> str:
        return f"Simulated response to: {prompt[:50]}..."

    def is_available(self) -> bool:
        return True

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": "simulated",
            "model": self.model_name,
            "type": "local_sim",
            "simulated": True,
        }
