"""
FreeLLMAPI AI Provider for JARVIS OS.
Connects JARVIS to the local FreeLLMAPI gateway (default: http://localhost:3001/v1).
Features:
- Live dynamic model catalog discovery from /v1/models with short caching & offline fallback.
- Full OpenAI-compatible chat completion and streaming SSE support.
- Native OpenAI tool calling + safe fallback parser for free models that emit inline tool syntax.
- Zero hardcoded secrets: reads FREELLMAPI_BASE_URL and FREELLMAPI_API_KEY strictly from env.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from typing import Any, Dict, Generator, List, Optional, Tuple, Union
import requests

from ai.providers.base import AIProvider, _chat_messages
from ai.providers.credentials import usable_key

logger = logging.getLogger("JARVIS.AI.FreeLLMAPI")

# Built-in offline fallback models when gateway cannot be contacted
OFFLINE_FALLBACK_MODELS = [
    "auto",
    "fusion",
    "gpt-4o",
    "claude-opus-4-5",
    "claude-sonnet-4-5",
    "claude-haiku-4-5",
    "qwen3.8-27b",
    "gpt-oss-120b",
    "gpt-oss-20b",
    "nemotron-3.5-super-vl",
    "nemotron-3-ultra-550b",
]


class FreeLLMAPIProvider(AIProvider):
    """JARVIS Provider implementation for FreeLLMAPI gateway."""
    name: str = "freellmapi"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 45.0,
        enabled: bool = True,
    ) -> None:
        raw_key = api_key if api_key is not None else os.getenv("FREELLMAPI_API_KEY", "")
        self.api_key = raw_key.strip() if raw_key else ""
        raw_url = base_url or os.getenv("FREELLMAPI_BASE_URL", "http://localhost:3001/v1")
        self.base_url = raw_url.rstrip("/")
        self.model = model or os.getenv("FREELLMAPI_MODEL", "auto")
        self.timeout = timeout
        self.enabled = enabled

        # Model catalog cache: (timestamp, [model_ids])
        self._models_cache: Optional[Tuple[float, List[str]]] = None
        self._models_cache_ttl: float = 60.0  # seconds

        # Availability probe cache: (timestamp, bool)
        self._avail_cache: Optional[Tuple[float, bool]] = None
        self._avail_cache_ttl: float = 15.0  # seconds

    @property
    def masked_key(self) -> str:
        """Return safe masked representation of the API key without revealing secrets."""
        if not self.api_key:
            return ""
        if len(self.api_key) <= 10:
            return "[CONFIGURED]"
        return f"{self.api_key[:6]}...{self.api_key[-4:]}"

    def to_dict(self) -> Dict[str, Any]:
        """Return safe serialization of the provider without leaking secrets."""
        return {
            "name": self.name,
            "base_url": self.base_url,
            "model": self.model,
            "enabled": self.enabled,
            "available": self.is_available(),
            "configured": bool(self.api_key and usable_key(self.api_key)),
            "masked_key": self.masked_key,
        }

    def is_available(self) -> bool:
        """Check if FreeLLMAPI is enabled, key is usable, and gateway is reachable."""
        if not self.enabled:
            return False
        if not usable_key(self.api_key):
            return False

        now = time.monotonic()
        if self._avail_cache and (now - self._avail_cache[0]) < self._avail_cache_ttl:
            return self._avail_cache[1]

        # Quick probe against /v1/models
        available = False
        try:
            url = f"{self.base_url}/models"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            }
            res = requests.get(url, headers=headers, timeout=2.5)
            available = (res.status_code == 200)
        except Exception as e:
            logger.debug("FreeLLMAPI reachability probe failed: %s", e)
            available = False

        self._avail_cache = (now, available)
        return available

    def list_models(self) -> List[str]:
        """Dynamically fetch the live catalog of available models from FreeLLMAPI with TTL cache."""
        now = time.monotonic()
        if self._models_cache and (now - self._models_cache[0]) < self._models_cache_ttl:
            return self._models_cache[1]

        if not usable_key(self.api_key):
            return [self.model] if self.model else ["auto"]

        try:
            url = f"{self.base_url}/models"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            }
            # Query models with available=true if possible, or all models
            res = requests.get(url, headers=headers, timeout=4.0)
            if res.status_code == 200:
                data = res.json()
                raw_models = data.get("data", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                discovered: List[str] = []
                for m in raw_models:
                    if isinstance(m, dict) and "id" in m:
                        discovered.append(m["id"])
                    elif isinstance(m, str):
                        discovered.append(m)

                if discovered:
                    if "auto" not in discovered:
                        discovered.insert(0, "auto")
                    # Put 'auto' and 'fusion' at the very top if present
                    priority = ["auto", "fusion"]
                    top = [p for p in priority if p in discovered]
                    rest = [p for p in discovered if p not in top]
                    final_list = top + rest
                    self._models_cache = (now, final_list)
                    return final_list
        except Exception as e:
            logger.warning("Failed to fetch live FreeLLMAPI model catalog: %s. Using fallback list.", e)

        # Fallback to previous cache or safe offline list
        if self._models_cache:
            return self._models_cache[1]
        fallback = list(OFFLINE_FALLBACK_MODELS)
        if self.model and self.model not in fallback:
            fallback.insert(0, self.model)
        return fallback

    def parse_fallback_tool_calls(
        self,
        text: str,
        advertised_tools: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Safe fallback parser for free models that emit tool syntax in text instead of native tool_calls."""
        if not text:
            return []

        calls: List[Dict[str, Any]] = []
        known_names = {t.get("name") for t in (advertised_tools or []) if isinstance(t, dict) and t.get("name")}

        # 1. XML style: <tool_call>{"name": "...", "arguments": {...}}</tool_call>
        xml_matches = re.findall(r'<tool_call>\s*({.*?})\s*</tool_call>', text, re.DOTALL)
        for raw in xml_matches:
            try:
                data = json.loads(raw)
                name = data.get("name") or data.get("tool") or data.get("function")
                args = data.get("arguments") or data.get("args") or data.get("parameters") or {}
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = {}
                if name and (not known_names or name in known_names):
                    calls.append({
                        "id": f"call_{uuid.uuid4().hex[:8]}",
                        "name": str(name).strip(),
                        "args": args if isinstance(args, dict) else {},
                    })
            except Exception:
                pass

        if calls:
            return calls

        # 2. Markdown fenced code blocks: ```json ... ``` or ```tool ... ```
        block_matches = re.findall(r'```(?:json|tool)?\s*({[\s\S]*?})\s*```', text)
        for raw in block_matches:
            try:
                data = json.loads(raw)
                name = data.get("name") or data.get("tool") or data.get("function")
                args = data.get("arguments") or data.get("args") or data.get("parameters") or {}
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = {}
                if name and (not known_names or name in known_names):
                    calls.append({
                        "id": f"call_{uuid.uuid4().hex[:8]}",
                        "name": str(name).strip(),
                        "args": args if isinstance(args, dict) else {},
                    })
            except Exception:
                pass

        if calls:
            return calls

        # 3. Direct JSON line: {"name": "...", "args": ...} or {"tool": "..."}
        try:
            trimmed = text.strip()
            if trimmed.startswith("{") and trimmed.endswith("}"):
                data = json.loads(trimmed)
                name = data.get("name") or data.get("tool") or data.get("function")
                args = data.get("arguments") or data.get("args") or data.get("parameters") or {}
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = {}
                if name and (not known_names or name in known_names):
                    calls.append({
                        "id": f"call_{uuid.uuid4().hex[:8]}",
                        "name": str(name).strip(),
                        "args": args if isinstance(args, dict) else {},
                    })
        except Exception:
            pass

        return calls

    def generate(
        self,
        messages: Union[List[Dict], str],
        tools: Optional[List[Dict]] = None,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """Execute chat completion against FreeLLMAPI gateway with tool calling & fallback parsing."""
        if not self.is_available():
            err = f"{self.name} gateway is not available or unconfigured at {self.base_url}"
            return None if isinstance(messages, str) else {"text": "", "tool_calls": [], "error": err, "http_status": 503}

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Normalize messages
        oai_messages = []
        if isinstance(messages, str):
            context = kwargs.get("context", {})
            sys_prompt = context.get("system_prompt") or context.get("system") or system
            if sys_prompt:
                oai_messages.append({"role": "system", "content": sys_prompt})
            oai_messages.append({"role": "user", "content": messages})
        else:
            if system:
                oai_messages.append({"role": "system", "content": system})
            oai_messages.extend(_chat_messages(messages))

        target_model = kwargs.get("model") or self.model or "auto"
        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": oai_messages,
            "temperature": kwargs.get("temperature", 0.7),
        }

        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]

        if tools:
            payload["tools"] = [
                {"type": "function", "function": t} if "function" not in t else t
                for t in tools
            ]

        req_timeout = min(self.timeout, float(kwargs.get("request_timeout", self.timeout)))

        try:
            r = requests.post(url, headers=headers, json=payload, timeout=req_timeout)
            if r.status_code == 200:
                data = r.json()
                choice = data.get("choices", [{}])[0]
                msg = choice.get("message", {})
                content = msg.get("content") or ""

                calls: List[Dict[str, Any]] = []
                for call in msg.get("tool_calls") or []:
                    fn = call.get("function", {})
                    fn_name = fn.get("name", "")
                    raw_args = fn.get("arguments", "{}")
                    try:
                        args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                    except Exception:
                        args = {}
                    calls.append({
                        "id": call.get("id") or f"call_{uuid.uuid4().hex[:8]}",
                        "name": fn_name,
                        "args": args if isinstance(args, dict) else {},
                    })

                # Safe fallback parsing if model emitted tool syntax in text
                if not calls and tools and content:
                    parsed_fallback = self.parse_fallback_tool_calls(content, advertised_tools=tools)
                    if parsed_fallback:
                        calls = parsed_fallback

                if isinstance(messages, str):
                    return content

                asst_msg: Dict[str, Any] = {"role": "assistant", "content": content}
                if calls:
                    asst_msg["tool_calls"] = [
                        {
                            "id": c["id"],
                            "type": "function",
                            "function": {"name": c["name"], "arguments": json.dumps(c["args"])},
                        }
                        for c in calls
                    ]

                return {
                    "text": content,
                    "tool_calls": calls,
                    "provider": self.name,
                    "model": target_model,
                    "tokens": data.get("usage", {}).get("total_tokens", 0),
                    "assistant_message": asst_msg,
                }

            # Handle non-200 responses truthfully
            err_msg = f"{self.name} returned HTTP {r.status_code}"
            try:
                err_data = r.json()
                if "error" in err_data:
                    err_msg += f": {err_data['error'].get('message', err_data['error'])}"
            except Exception:
                pass

            logger.warning("FreeLLMAPI error: %s", err_msg)
            return None if isinstance(messages, str) else {
                "text": "",
                "tool_calls": [],
                "error": err_msg,
                "http_status": r.status_code,
            }

        except Exception as e:
            logger.warning("FreeLLMAPI request failed: %s (%s)", type(e).__name__, e)
            return None if isinstance(messages, str) else {
                "text": "",
                "tool_calls": [],
                "error": f"{self.name} request failed ({type(e).__name__})",
            }

    def stream_generate(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream chat tokens in real-time using SSE from FreeLLMAPI gateway."""
        if not self.is_available():
            yield {"token": "", "done": True, "error": f"{self.name} gateway unavailable", "provider": self.name, "model": self.model}
            return

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        oai_messages = []
        if system:
            oai_messages.append({"role": "system", "content": system})
        oai_messages.extend(_chat_messages(messages))

        target_model = kwargs.get("model") or self.model or "auto"
        payload = {
            "model": target_model,
            "messages": oai_messages,
            "stream": True,
            "temperature": kwargs.get("temperature", 0.7),
        }
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]

        completed = False
        try:
            req_timeout = min(self.timeout, float(kwargs.get("request_timeout", self.timeout)))
            r = requests.post(url, headers=headers, json=payload, stream=True, timeout=req_timeout)
            r.raise_for_status()

            for line in r.iter_lines():
                if not line:
                    continue
                decoded = line.decode("utf-8")
                if decoded.startswith("data: "):
                    body = decoded[6:].strip()
                    if body == "[DONE]":
                        completed = True
                        yield {"token": "", "done": True, "provider": self.name, "model": target_model}
                        break
                    try:
                        chunk = json.loads(body)
                        choices = chunk.get("choices") or []
                        if not choices:
                            continue
                        choice = choices[0]
                        delta = choice.get("delta", {}).get("content", "")
                        if delta:
                            yield {"token": delta, "done": False, "provider": self.name, "model": target_model}
                        reason = choice.get("finish_reason")
                        if reason and reason != "stop":
                            yield {"token": "", "done": True, "provider": self.name, "model": target_model}
                            return
                        if reason == "stop":
                            completed = True
                    except Exception:
                        pass

            if not completed:
                yield {"token": "", "done": True, "provider": self.name, "model": target_model}

        except Exception as e:
            logger.error("FreeLLMAPI stream error: %s", e)
            yield {"token": "", "done": True, "error": f"{self.name} stream error ({type(e).__name__})", "provider": self.name, "model": target_model}
