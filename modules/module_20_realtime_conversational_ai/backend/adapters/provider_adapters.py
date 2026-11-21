"""Configurable AI provider adapters with streaming & error recovery (Module 20)."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List

import httpx

PERSONA_PROFILES: Dict[str, Dict[str, Any]] = {
    "aria": {
        "id": "aria",
        "name": "ARIA",
        "gender": "female",
        "accent_color": "#00D9FF",
        "secondary_color": "#9868FF",
        "voice_pitch": 1.12,
        "voice_rate": 1.02,
        "preferred_voice_keywords": ["female", "samantha", "victoria", "zira", "google us english"],
        "tagline": "Adaptive Responsive Intelligence Avatar — Warm, analytical, voice-first guide.",
    },
    "atlas": {
        "id": "atlas",
        "name": "ATLAS",
        "gender": "male",
        "accent_color": "#218BFF",
        "secondary_color": "#25E6A2",
        "voice_pitch": 0.88,
        "voice_rate": 0.98,
        "preferred_voice_keywords": ["male", "daniel", "alex", "david", "google uk english male"],
        "tagline": "Autonomous Tactical Logic & Systems Avatar — Calm, crisp, systems-focused.",
    },
}


class ConversationalProviderAdapter(ABC):
    provider_name: str = "abstract"
    is_simulated: bool = True

    @abstractmethod
    async def stream_reply(
        self,
        messages: List[Dict[str, str]],
        persona: str,
        model: str,
    ) -> AsyncIterator[str]:
        raise NotImplementedError
        yield ""  # pragma: no cover


class SimulatedLocalProvider(ConversationalProviderAdapter):
    """Deterministic local conversational simulator — works completely offline."""

    provider_name = "simulated_local"
    is_simulated = True

    async def stream_reply(
        self,
        messages: List[Dict[str, str]],
        persona: str,
        model: str,
    ) -> AsyncIterator[str]:
        last_user = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user = m.get("content", "")
                break
        pname = PERSONA_PROFILES.get(persona, PERSONA_PROFILES["aria"])["name"]
        turn_count = sum(1 for m in messages if m.get("role") == "user")
        low = last_user.lower()

        if "status" in low or "health" in low:
            reply = (
                f"{pname} online in local simulation mode. Turn {turn_count} active with "
                f"{len(messages)} context messages retained. All voice controls, subtitles, and "
                f"approximate viseme lip-sync are operational."
            )
        elif "hello" in low or "hi" in low or "jarvis" in low:
            reply = (
                f"Hello! I am {pname}, your JARVIS holographic conversational interface. "
                f"You can speak using your microphone, interrupt me mid-sentence, or switch between ARIA and ATLAS anytime."
            )
        else:
            reply = (
                f"[{pname} · Simulated Local Provider] I received your message: \"{last_user[:140]}\". "
                f"Context window currently holds {len(messages)} turn(s). Configure Ollama or an OpenAI-compatible "
                f"endpoint in settings to route live LLM completions."
            )

        for token in reply.split(" "):
            await asyncio.sleep(0.015)
            yield token + " "


class OpenAICompatibleProvider(ConversationalProviderAdapter):
    """Generic HTTP adapter for OpenAI-compatible / Ollama / OpenRouter endpoints."""

    provider_name = "openai_compatible"
    is_simulated = False

    def __init__(self, base_url: str, api_key: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def stream_reply(
        self,
        messages: List[Dict[str, str]],
        persona: str,
        model: str,
    ) -> AsyncIterator[str]:
        if not self.base_url:
            raise RuntimeError("Provider URL is not configured for openai_compatible adapter.")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={"model": model, "messages": messages, "stream": False},
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            for word in text.split(" "):
                yield word + " "
