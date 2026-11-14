"""
JARVIS llama-cpp-python Provider
Runs local GGUF models directly without Ollama.
Works on ARM64 (Raspberry Pi 5) with CPU inference.
"""
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Union

from ai.providers.base import AIProvider

logger = logging.getLogger("JARVIS.AI.LlamaCpp")

GGUF_SEARCH_PATHS = [
    os.path.expanduser("~/.ollama/models"),
    os.path.expanduser("~/models"),
    "/opt/jarvis-os/models",
    "/home/pi/models",
    os.path.join(os.path.dirname(__file__), "../../models"),
]


class LlamaCppProvider(AIProvider):
    """Local inference using llama-cpp-python (no Ollama needed)."""
    name = "llama_cpp"

    def __init__(
        self,
        model_path: Optional[str] = None,
        n_ctx: int = 2048,
        n_threads: int = 4,
        enabled: bool = True,
    ) -> None:
        self._model_path = model_path
        self._n_ctx = n_ctx
        self._n_threads = n_threads
        self._llm = None
        self.model = "llama-cpp-python"
        self.enabled = enabled

    @property
    def model_path(self) -> Optional[str]:
        if self._model_path and os.path.exists(self._model_path):
            return self._model_path
        # Auto-discover GGUF files
        for path in GGUF_SEARCH_PATHS:
            if not os.path.isdir(path):
                continue
            for root, _dirs, files in os.walk(path):
                for f in files:
                    if f.endswith(".gguf"):
                        found = os.path.join(root, f)
                        logger.info("Auto-discovered model: %s", found)
                        return found
        return None

    def is_available(self) -> bool:
        if not self.enabled:
            return False
        try:
            import llama_cpp  # noqa: F401
            return bool(self.model_path)
        except Exception:
            return False

    def list_models(self) -> List[str]:
        path = self.model_path
        return [os.path.basename(path)] if path else []

    def _get_llm(self):
        if self._llm is None:
            from llama_cpp import Llama

            path = self.model_path
            if not path:
                raise FileNotFoundError("No GGUF model path available")
            logger.info("Loading model: %s", path)
            self._llm = Llama(
                model_path=path,
                n_ctx=self._n_ctx,
                n_threads=self._n_threads,
                verbose=False,
            )
            self.model = os.path.basename(path)
        return self._llm

    def generate(
        self,
        messages: Union[List[Dict], str],
        tools: Optional[List[Dict]] = None,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        if not self.enabled:
            return None if isinstance(messages, str) else {
                "text": "",
                "tool_calls": [],
                "provider": self.name,
                "model": self.model,
                "tokens": 0,
                "error": "Provider disabled",
            }
        if not self.is_available():
            err = "llama-cpp-python or GGUF model not available"
            return None if isinstance(messages, str) else {
                "text": "",
                "tool_calls": [],
                "provider": self.name,
                "model": self.model,
                "tokens": 0,
                "error": err,
            }

        try:
            llm = self._get_llm()

            # Normalize messages
            if isinstance(messages, str):
                context = kwargs.get("context", {}) or {}
                sys_prompt = context.get("system_prompt") or context.get("system") or system
                msg_list = [{"role": "user", "content": messages}]
            else:
                sys_prompt = system
                msg_list = messages

            parts = []
            if sys_prompt:
                parts.append(f"<|system|>\n{sys_prompt}")
            for m in msg_list:
                role = m.get("role", "user")
                content = m.get("content", "")
                if role == "user":
                    parts.append(f"<|user|>\n{content}")
                elif role == "assistant":
                    parts.append(f"<|assistant|>\n{content}")
                elif role == "tool":
                    parts.append(f"<|tool_result|>\n{content}")
                elif role == "system" and not sys_prompt:
                    parts.append(f"<|system|>\n{content}")

            if tools:
                tool_desc = "\n".join(f"- {t.get('name')}: {t.get('description', '')}" for t in tools)
                parts.append(
                    f"<|user|>\nYou have access to these tools:\n{tool_desc}\n"
                    "To call a tool, write: TOOL_CALL: {\"name\": \"...\", \"args\": {...}}"
                )

            parts.append("<|assistant|>")
            prompt = "\n".join(parts)

            result = llm(
                prompt,
                max_tokens=int(kwargs.get("max_tokens", 512)),
                temperature=float(kwargs.get("temperature", 0.7)),
                stop=["<|user|>", "<|system|>", "</s>"],
                echo=False,
            )
            text = (result.get("choices", [{}])[0].get("text") or "").strip()

            tool_calls = []
            for m in re.finditer(r'TOOL_CALL:\s*(\{.*?\})', text, re.DOTALL):
                try:
                    data = json.loads(m.group(1))
                    if isinstance(data, dict) and "name" in data:
                        tool_calls.append({"name": data.get("name"), "args": data.get("args", {})})
                except Exception:
                    pass
            if tool_calls and "TOOL_CALL:" in text:
                text = text[:text.find("TOOL_CALL:")].strip()

            if isinstance(messages, str):
                return text

            return {
                "text": text,
                "tool_calls": tool_calls,
                "provider": self.name,
                "model": self.model,
                "tokens": (result.get("usage", {}) or {}).get("total_tokens", 0),
            }
        except Exception as e:
            logger.error("LlamaCpp error: %s", e)
            if isinstance(messages, str):
                return None
            return {
                "text": "",
                "tool_calls": [],
                "provider": self.name,
                "model": self.model,
                "tokens": 0,
                "error": str(e),
            }

    def get_model_info(self) -> Dict[str, Any]:
        path = self.model_path
        return {
            "name": self.name,
            "model": self.model,
            "enabled": self.enabled,
            "available": self.is_available(),
            "model_path": path,
            "task_preference": ["local", "offline"],
        }
