"""Zero-extra-dependency LLM client for OpenRouter, Local Ollama, and Offline Fallback."""

from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

from .config import CodingAssistantConfig


@dataclass
class LLMCompletion:
    text: str
    provider_used: str
    used_fallback: bool
    manual_prompt_fallback: Optional[str] = None


class CodingLLMClient:
    """Async LLM router supporting OpenRouter (JARVIS default), Local Ollama, and offline fallback."""

    def __init__(self, config: CodingAssistantConfig) -> None:
        self.config = config

    async def complete(self, system_prompt: str, user_prompt: str) -> LLMCompletion:
        """Attempt configured AI provider; return fallback marker if unavailable."""
        mode = self.config.provider
        manual_export = (
            "=== SYSTEM PROMPT ===\n"
            f"{system_prompt}\n\n"
            "=== USER PROMPT ===\n"
            f"{user_prompt}\n"
        )

        if mode == "offline":
            return LLMCompletion(
                text="",
                provider_used="offline-local",
                used_fallback=True,
                manual_prompt_fallback=manual_export,
            )

        if mode in ("auto", "openrouter") and self.config.openrouter_api_key:
            result = await asyncio.to_thread(
                self._call_openrouter_sync, system_prompt, user_prompt
            )
            if result:
                return LLMCompletion(
                    text=result,
                    provider_used=f"openrouter:{self.config.openrouter_model}",
                    used_fallback=False,
                )

        if mode in ("auto", "ollama"):
            result = await asyncio.to_thread(
                self._call_ollama_sync, system_prompt, user_prompt
            )
            if result:
                return LLMCompletion(
                    text=result,
                    provider_used=f"ollama:{self.config.ollama_model}",
                    used_fallback=False,
                )

        return LLMCompletion(
            text="",
            provider_used="offline-local",
            used_fallback=True,
            manual_prompt_fallback=manual_export,
        )

    def _call_openrouter_sync(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        payload = json.dumps(
            {
                "model": self.config.openrouter_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            self.config.openrouter_base_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.openrouter_api_key}",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "JARVIS OS AI Coding Assistant",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.request_timeout_sec) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choices = data.get("choices") or []
                if choices:
                    return str(choices[0]["message"]["content"]).strip()
        except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError, OSError):
            return None
        return None

    def _call_ollama_sync(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        url = f"{self.config.ollama_base_url.rstrip('/')}/api/chat"
        payload = json.dumps(
            {
                "model": self.config.ollama_model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.request_timeout_sec) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                message = data.get("message") or {}
                content = message.get("content")
                if content:
                    return str(content).strip()
        except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError, OSError):
            return None
        return None
