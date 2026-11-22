"""Zero-extra-dependency LLM client for OpenAI ChatGPT, OpenRouter, Ollama, and offline KB fallback."""

from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

from .config import SupportBotConfig


@dataclass
class LLMOutput:
    text: str
    provider_used: str
    used_fallback: bool


class SupportLLMClient:
    """Async LLM router supporting OpenAI ChatGPT, OpenRouter, Ollama, and offline KB fallback."""

    def __init__(self, config: SupportBotConfig) -> None:
        self.config = config

    async def complete(self, system_prompt: str, user_prompt: str) -> LLMOutput:
        mode = self.config.provider
        if mode == "offline":
            return LLMOutput(text="", provider_used="offline-kb", used_fallback=True)

        if mode in ("auto", "openai") and self.config.openai_api_key:
            text = await asyncio.to_thread(
                self._call_chat_completions_sync,
                "https://api.openai.com/v1/chat/completions",
                self.config.openai_api_key,
                self.config.openai_model,
                system_prompt,
                user_prompt,
            )
            if text:
                return LLMOutput(text=text, provider_used=f"openai:{self.config.openai_model}", used_fallback=False)

        if mode in ("auto", "openrouter") and self.config.openrouter_api_key:
            text = await asyncio.to_thread(
                self._call_chat_completions_sync,
                "https://openrouter.ai/api/v1/chat/completions",
                self.config.openrouter_api_key,
                self.config.openrouter_model,
                system_prompt,
                user_prompt,
            )
            if text:
                return LLMOutput(
                    text=text,
                    provider_used=f"openrouter:{self.config.openrouter_model}",
                    used_fallback=False,
                )

        if mode in ("auto", "ollama"):
            text = await asyncio.to_thread(self._call_ollama_sync, system_prompt, user_prompt)
            if text:
                return LLMOutput(text=text, provider_used=f"ollama:{self.config.ollama_model}", used_fallback=False)

        return LLMOutput(text="", provider_used="offline-kb", used_fallback=True)

    def _call_chat_completions_sync(
        self,
        url: str,
        api_key: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
    ) -> Optional[str]:
        payload = json.dumps(
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.3,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
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
                msg = data.get("message") or {}
                if msg.get("content"):
                    return str(msg["content"]).strip()
        except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError, OSError):
            return None
        return None
