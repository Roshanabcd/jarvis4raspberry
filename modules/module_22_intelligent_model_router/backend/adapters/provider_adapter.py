"""Provider adapter contract and clearly labeled SimulatedModelProviderAdapter for Module 22."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class ProviderInvocationError(Exception):
    """Raised when a model provider fails or times out."""


class ModelProviderAdapter(ABC):
    adapter_name: str = "abstract"
    is_simulated: bool = True

    @abstractmethod
    def invoke(self, model: Dict[str, Any], prompt: str, task_type: str) -> Dict[str, Any]:
        """Execute a completion against the target model and return text, tokens, and latency."""
        raise NotImplementedError


def estimate_tokens(text: str) -> int:
    return max(1, int(len(text.split()) * 1.35))


class SimulatedModelProviderAdapter(ModelProviderAdapter):
    """Safe offline simulation adapter for local testing without live LLM credentials."""

    adapter_name = "simulated_model_provider"
    is_simulated = True

    def invoke(self, model: Dict[str, Any], prompt: str, task_type: str) -> Dict[str, Any]:
        if model.get("simulate_outage"):
            raise ProviderInvocationError(
                f"[SIMULATED OUTAGE] Provider '{model['provider']}' / model '{model['model_id']}' is temporarily unavailable."
            )

        in_tokens = estimate_tokens(prompt)
        snippet = prompt.strip().replace("\n", " ")[:140]
        response_text = (
            f"[SIMULATED {model['display_name']} | task={task_type}] "
            f"Processed request ({in_tokens} est. input tokens): \"{snippet}\". "
            f"Configure a live ModelProviderAdapter (Ollama/Gemini/OpenAI/Anthropic) for real LLM completions."
        )
        out_tokens = estimate_tokens(response_text)
        cost_usd = round(
            (in_tokens / 1000.0) * float(model["cost_per_1k_input_usd"])
            + (out_tokens / 1000.0) * float(model["cost_per_1k_output_usd"]),
            6,
        )
        return {
            "simulated": True,
            "model_id": model["model_id"],
            "provider": model["provider"],
            "response_text": response_text,
            "input_tokens": in_tokens,
            "output_tokens": out_tokens,
            "cost_usd": cost_usd,
            "latency_ms": int(model["avg_latency_ms"]),
        }
