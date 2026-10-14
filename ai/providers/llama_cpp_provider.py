"""
JARVIS llama-cpp-python Provider
Runs local GGUF models directly without Ollama.
Works on ARM64 (Raspberry Pi 5) with CPU inference.
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("JARVIS.AI.LlamaCpp")

GGUF_SEARCH_PATHS = [
    os.path.expanduser("~/.ollama/models"),
    os.path.expanduser("~/models"),
    "/opt/jarvis-os/models",
    "/home/pi/models",
    os.path.join(os.path.dirname(__file__), "../../models"),
]


class LlamaCppProvider:
    """Local inference using llama-cpp-python (no Ollama needed)."""
    name = "llama_cpp"

    def __init__(self, model_path: Optional[str] = None, n_ctx: int = 2048,
                 n_threads: int = 4) -> None:
        self._model_path = model_path
        self._n_ctx = n_ctx
        self._n_threads = n_threads
        self._llm = None
        self.model = "llama-cpp-python"

    @property
    def model_path(self) -> Optional[str]:
        if self._model_path and os.path.exists(self._model_path):
            return self._model_path
        # Auto-discover GGUF files
        for path in GGUF_SEARCH_PATHS:
            if not os.path.isdir(path):
                continue
            for root, dirs, files in os.walk(path):
                for f in files:
                    if f.endswith(".gguf"):
                        found = os.path.join(root, f)
                        logger.info(f"Auto-discovered model: {found}")
                        return found
        return None

    def is_available(self) -> bool:
        try:
            import llama_cpp  # noqa
            return bool(self.model_path)
        except ImportError:
            return False

    def _get_llm(self):
        if self._llm is None:
            from llama_cpp import Llama
            path = self.model_path
            logger.info(f"Loading model: {path}")
            self._llm = Llama(
                model_path=path,
                n_ctx=self._n_ctx,
                n_threads=self._n_threads,
                verbose=False,
            )
            self.model = os.path.basename(path)
        return self._llm

    def generate(self, messages: List[Dict], tools: Optional[List] = None,
                 system: Optional[str] = None) -> Dict[str, Any]:
        try:
            llm = self._get_llm()

            # Build prompt
            parts = []
            if system:
                parts.append(f"<|system|>\n{system}")
            for m in messages:
                role = m.get("role", "user")
                content = m.get("content", "")
                if role == "user":
                    parts.append(f"<|user|>\n{content}")
                elif role == "assistant":
                    parts.append(f"<|assistant|>\n{content}")
                elif role == "tool":
                    parts.append(f"<|tool_result|>\n{content}")

            if tools:
                tool_desc = "\n".join(f"- {t['name']}: {t['description']}" for t in tools)
                parts.append(
                    f"<|user|>\nYou have access to these tools:\n{tool_desc}\n"
                    "To call a tool, write: TOOL_CALL: {\"name\": \"...\", \"args\": {...}}"
                )

            parts.append("<|assistant|>")
            prompt = "\n".join(parts)

            result = llm(
                prompt,
                max_tokens=512,
                temperature=0.7,
                stop=["<|user|>", "<|system|>", "</s>"],
                echo=False,
            )
            text = result["choices"][0]["text"].strip()

            # Extract tool calls
            import re
            tool_calls = []
            for m in re.finditer(r'TOOL_CALL:\s*(\{.*?\})', text, re.DOTALL):
                try:
                    data = json.loads(m.group(1))
                    tool_calls.append({"name": data.get("name"), "args": data.get("args", {})})
                except Exception:
                    pass
            if tool_calls:
                text = text[:text.find("TOOL_CALL:")].strip()

            return {
                "text": text,
                "tool_calls": tool_calls,
                "provider": "llama_cpp",
                "model": self.model,
                "tokens": result.get("usage", {}).get("total_tokens", 0),
            }
        except Exception as e:
            logger.error(f"LlamaCpp error: {e}")
            return {"text": "", "tool_calls": [], "provider": "llama_cpp",
                    "model": self.model, "tokens": 0, "error": str(e)}
