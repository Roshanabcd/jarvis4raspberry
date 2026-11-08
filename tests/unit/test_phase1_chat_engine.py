"""Unit tests for Phase 1: Real AI Chat Engine & Multi-Provider Architecture."""

import json
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from ai.providers.base import (
    AIProvider,
    OllamaProvider,
    GeminiProvider,
    OpenAIProvider,
    AnthropicProvider,
    NvidiaNimProvider,
    GenericOpenAIProvider,
)
from ai.brain import JARVISBrain
from apps.core.main import app


class TestMultiProviderRegistry:
    """Verify all required provider adapters conform to AIProvider interface."""

    def test_provider_subclasses_exist(self):
        providers = [
            OllamaProvider,
            GeminiProvider,
            OpenAIProvider,
            AnthropicProvider,
            NvidiaNimProvider,
            GenericOpenAIProvider,
        ]
        for cls in providers:
            assert issubclass(cls, AIProvider), f"{cls.__name__} must subclass AIProvider"

    def test_ollama_discovery_and_model_list(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "models": [{"name": "llama3.2:1b"}, {"name": "qwen3.5:4b"}]
            }
            provider = OllamaProvider(base_url="http://127.0.0.1:11434")
            assert provider.is_available() is True
            models = provider.list_models()
            assert "llama3.2:1b" in models
            assert "qwen3.5:4b" in models
            assert provider.model == "llama3.2:1b"

    def test_ollama_stream_generate(self):
        provider = OllamaProvider(base_url="http://127.0.0.1:11434", model="llama3.2:1b")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            json.dumps({"message": {"content": "Hello"}, "done": False}).encode(),
            json.dumps({"message": {"content": " Roshan"}, "done": False}).encode(),
            json.dumps({"message": {"content": "!"}, "done": True, "eval_count": 3}).encode(),
        ]

        with patch("requests.post", return_value=mock_response):
            chunks = list(provider.stream_generate([{"role": "user", "content": "hi"}]))
            assert len(chunks) == 3
            text = "".join(c.get("token", "") for c in chunks)
            assert text == "Hello Roshan!"
            assert chunks[-1]["done"] is True

    def test_gemini_provider_availability(self):
        prov_no_key = GeminiProvider(api_key="")
        assert prov_no_key.is_available() is False

        prov_with_key = GeminiProvider(api_key="AIzaSyDummyKey")
        assert prov_with_key.is_available() is True

    def test_openai_provider_streaming(self):
        provider = OpenAIProvider(api_key="sk-dummy", model="gpt-4o-mini")
        assert provider.is_available() is True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b"data: " + json.dumps({"choices": [{"delta": {"content": "Greetings"}}]}).encode(),
            b"data: [DONE]",
        ]

        with patch("requests.post", return_value=mock_response):
            chunks = list(provider.stream_generate([{"role": "user", "content": "hi"}]))
            assert len(chunks) == 2
            assert chunks[0]["token"] == "Greetings"
            assert chunks[1]["done"] is True

    def test_nvidia_nim_provider(self):
        nim = NvidiaNimProvider(api_key="nvapi-dummy", model="meta/llama-3.1-70b-instruct")
        assert nim.is_available() is True
        assert nim.base_url == "https://integrate.api.nvidia.com/v1"

    def test_generic_openai_provider(self):
        custom = GenericOpenAIProvider(
            name="groq",
            base_url="https://api.groq.com/openai/v1",
            api_key="gsk-dummy",
            model="llama-3.1-8b-instant",
        )
        assert custom.is_available() is True
        assert custom.name == "groq"
        assert custom.model == "llama-3.1-8b-instant"


class TestChatEndpoints:
    """Verify synchronous, streaming, and provider management endpoints."""

    def setup_method(self):
        self.client = TestClient(app)

    def test_get_providers_status(self):
        res = self.client.get("/api/chat/providers")
        assert res.status_code == 200
        data = res.json()
        assert "providers" in data
        assert "active_provider" in data
        assert "active_model" in data
        provider_names = [p["name"] for p in data["providers"]]
        assert "ollama" in provider_names

    def test_switch_model_endpoint(self):
        res = self.client.post("/api/chat/model", json={"provider": "ollama", "model": "llama3.2:1b"})
        assert res.status_code == 200
        data = res.json()
        assert data["active_provider"] == "ollama"
        assert data["active_model"] == "llama3.2:1b"

    def test_chat_streaming_sse_endpoint(self):
        with patch.object(JARVISBrain, "stream_chat") as mock_stream:
            def mock_gen(*args, **kwargs):
                yield {"type": "start", "provider": "ollama", "model": "llama3.2:1b"}
                yield {"type": "token", "content": "Hello"}
                yield {"type": "token", "content": " World"}
                yield {"type": "done", "provider": "ollama", "model": "llama3.2:1b"}

            mock_stream.side_effect = mock_gen
            res = self.client.post("/api/chat/stream", json={"message": "hello jarvis"})
            assert res.status_code == 200
            assert "text/event-stream" in res.headers["content-type"]
            body = res.text
            assert "data: " in body
            assert "Hello" in body
            assert "World" in body
