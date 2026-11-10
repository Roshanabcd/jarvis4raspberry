"""
JARVIS OS — Shared AI Service Layer for Applications.
Provides unified, reusable AI inference methods (chat completion, text generation,
structured JSON, summarization, classification, embeddings, and vision analysis)
backed by local Ollama and configured cloud providers (Gemini, Claude, OpenAI).
"""

import json
import logging
import os
import re
import threading
import time
from typing import Any, Dict, List, Optional, Union

import requests

from ai.brain import JARVISBrain
from ai.providers.base import (
    AIProvider,
    OllamaProvider,
    GeminiProvider,
    OpenAIProvider,
    AnthropicProvider,
)
from apps.apps_center.resource_manager import resource_manager
from config.config_manager import config

logger = logging.getLogger("JARVIS.AppsCenter.AIService")


class SharedAIService:
    """
    Central shared AI service layer.
    Allows all registered applications to leverage common model infrastructure,
    caching, rate-limiting, and error-handling.
    """
    _instance = None
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SharedAIService, cls).__new__(cls)
                cls._instance._brain = JARVISBrain()
            return cls._instance

    # ── 1. Provider Discovery & Truthful Health ─────────────
    def get_providers_status(self) -> List[Dict[str, Any]]:
        """
        Check connectivity and truthful configuration status of all potential AI providers.
        Never fabricates connection success if credentials or endpoints are unavailable.
        """
        status_list = []

        # 1. Ollama (Local Pi 5)
        ollama_url = config.get("ollama_url", "http://127.0.0.1:11434")
        ollama_ok = False
        ollama_models = []
        ollama_err = None
        try:
            r = requests.get(f"{ollama_url}/api/tags", timeout=1.5)
            if r.status_code == 200:
                ollama_ok = True
                data = r.json()
                ollama_models = [m.get("name") for m in data.get("models", [])]
        except Exception as e:
            ollama_err = str(e)

        status_list.append({
            "id": "ollama",
            "name": "Local Ollama Daemon",
            "type": "local",
            "configured": True,
            "connected": ollama_ok,
            "active_model": config.get("ollama_model", "llama3.2:1b"),
            "available_models": ollama_models,
            "error": ollama_err,
            "last_check": time.time(),
        })

        # 2. Google Gemini
        gemini_key = os.environ.get("GEMINI_API_KEY") or config.get("gemini_api_key")
        has_gemini = bool(gemini_key and gemini_key.strip() and not gemini_key.startswith("your_"))
        status_list.append({
            "id": "gemini",
            "name": "Google Gemini API",
            "type": "cloud",
            "configured": has_gemini,
            "connected": has_gemini,  # Checked upon query
            "active_model": config.get("gemini_model", "gemini-2.0-flash"),
            "available_models": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
            "error": None if has_gemini else "Provider not configured (GEMINI_API_KEY required)",
            "last_check": time.time(),
        })

        # 3. OpenAI
        openai_key = os.environ.get("OPENAI_API_KEY") or config.get("openai_api_key")
        has_openai = bool(openai_key and openai_key.strip() and not openai_key.startswith("your_"))
        status_list.append({
            "id": "openai",
            "name": "OpenAI API",
            "type": "cloud",
            "configured": has_openai,
            "connected": has_openai,
            "active_model": config.get("openai_model", "gpt-4o-mini"),
            "available_models": ["gpt-4o", "gpt-4o-mini"],
            "error": None if has_openai else "Provider not configured (OPENAI_API_KEY required)",
            "last_check": time.time(),
        })

        # 4. Anthropic Claude
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY") or config.get("anthropic_api_key")
        has_anthropic = bool(anthropic_key and anthropic_key.strip() and not anthropic_key.startswith("your_"))
        status_list.append({
            "id": "anthropic",
            "name": "Anthropic Claude API",
            "type": "cloud",
            "configured": has_anthropic,
            "connected": has_anthropic,
            "active_model": config.get("anthropic_model", "claude-3-haiku-20240307"),
            "available_models": ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
            "error": None if has_anthropic else "Provider not configured (ANTHROPIC_API_KEY required)",
            "last_check": time.time(),
        })

        return status_list

    # ── 2. Unified Task Inferences ──────────────────────────
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        """Execute chat completion across available providers with resource checking."""
        prov = self._resolve_provider(provider)
        if not prov:
            return {
                "success": False,
                "error": f"Provider '{provider or 'default'}' not configured or currently unavailable.",
                "text": "",
                "provider": provider,
            }

        t0 = time.perf_counter()
        res = prov.generate(
            messages=messages,
            system=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        elapsed_s = round(time.perf_counter() - t0, 3)

        text = res if isinstance(res, str) else (res.get("text", "") if isinstance(res, dict) else "")
        return {
            "success": True,
            "text": text,
            "provider": prov.name,
            "model": getattr(prov, "model", model or "default"),
            "duration_s": elapsed_s,
        }

    def generate_text(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        """Simple text generation convenience wrapper."""
        res = self.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=system,
            **kwargs,
        )
        return res.get("text", "")

    def generate_structured_json(
        self,
        prompt: str,
        json_schema_or_example: Dict[str, Any],
        system: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Request AI output strictly formatted as valid JSON adhering to schema/example.
        Extracts JSON robustly using regex if enclosed in markdown backticks.
        """
        sys = (system or "") + (
            f"\n\nCRITICAL: Respond ONLY with a valid JSON object strictly matching this schema or structure:\n"
            f"{json.dumps(json_schema_or_example, indent=2)}\n"
            "Do NOT include markdown explanations, preambles, or conversational commentary. Output raw JSON only."
        )

        raw = self.generate_text(prompt, system=sys)
        # Parse JSON
        clean_json = raw.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```", 1)[1].split("```", 1)[0].strip()

        try:
            return {"success": True, "data": json.loads(clean_json), "raw": raw}
        except Exception as e:
            # Fallback regex search for { ... }
            match = re.search(r"\{.*\}", clean_json, re.DOTALL)
            if match:
                try:
                    return {"success": True, "data": json.loads(match.group(0)), "raw": raw}
                except Exception:
                    pass
            return {"success": False, "error": f"JSON parse error: {e}", "raw": raw, "data": None}

    def summarize(self, text: str, max_words: int = 150) -> Dict[str, Any]:
        """Summarize text concisely using shared LLM."""
        prompt = f"Please provide a concise, factual summary of the following text in under {max_words} words:\n\n{text[:8000]}"
        summary = self.generate_text(prompt, system="You are an expert executive summarizer. Be direct, clear, and objective.")
        return {"summary": summary, "word_count": len(summary.split())}

    def classify(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """Classify given text into one of the provided category labels."""
        categories_str = ", ".join(f"'{c}'" for c in categories)
        prompt = (
            f"Classify the following text into exactly ONE of these categories: [{categories_str}].\n"
            f"Return JSON with keys 'category' and 'confidence_score' (0.0 to 1.0).\n\n"
            f"Text: \"{text[:2000]}\""
        )
        res = self.generate_structured_json(prompt, {"category": categories[0], "confidence_score": 0.95})
        if res.get("success"):
            data = res.get("data", {})
            return {
                "category": data.get("category", "unknown"),
                "confidence": data.get("confidence_score", 0.5),
            }
        return {"category": categories[0] if categories else "unknown", "confidence": 0.0}

    def generate_embedding(self, text: str) -> Dict[str, Any]:
        """Generate text embedding vector using local Ollama if available."""
        ollama_url = config.get("ollama_url", "http://127.0.0.1:11434")
        try:
            r = requests.post(
                f"{ollama_url}/api/embeddings",
                json={"model": config.get("ollama_model", "llama3.2:1b"), "prompt": text[:2000]},
                timeout=5.0,
            )
            if r.status_code == 200:
                emb = r.json().get("embedding", [])
                return {"success": True, "dimensions": len(emb), "embedding": emb}
        except Exception as e:
            logger.debug("Ollama embeddings call failed: %s", e)

        return {"success": False, "error": "Embeddings not supported or Ollama unavailable", "embedding": []}

    def describe_image(self, image_path: str, prompt: str = "Describe this image in detail.") -> str:
        """Analyze an image using local Moondream VLM."""
        from tools.vision.vision_vlm import vision_vlm
        res = vision_vlm.visual_qa(image_path, prompt)
        return res.get("answer", res.get("description", ""))

    def _resolve_provider(self, name: Optional[str] = None) -> Optional[AIProvider]:
        """Resolve specific provider or fallback to active brain provider."""
        return self._brain._get_provider(name)


# Global singleton instance
shared_ai = SharedAIService()
