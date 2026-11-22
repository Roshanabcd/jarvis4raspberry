"""Unit tests for FreeLLMAPI gateway provider, dynamic catalog, fallback tool parsing,
DeveloperCliBridge integration, PC tools, and PIN gating.
"""

import json
import time
from unittest.mock import MagicMock

import pytest

from ai.providers.freellmapi_provider import FreeLLMAPIProvider
from tools.developer.cli_bridge import DeveloperCliBridge, developer_cli_bridge
from tools.registry import ToolRegistry


# ─────────────────────────────────────────────────────────────────────────────
# 1. FreeLLMAPIProvider Initialization & Security
# ─────────────────────────────────────────────────────────────────────────────

def test_freellmapi_init_and_masked_key(monkeypatch):
    """Verify provider initializes and masks credentials securely."""
    mock_get = MagicMock()
    mock_resp = MagicMock(status_code=200)
    mock_get.return_value = mock_resp
    monkeypatch.setattr("ai.providers.freellmapi_provider.requests.get", mock_get)

    dummy_key = "flm_test_secret_key_1234567890"
    p = FreeLLMAPIProvider(
        api_key=dummy_key,
        base_url="http://localhost:3001/v1",
        model="auto",
    )
    assert p.name == "freellmapi"
    assert p.base_url == "http://localhost:3001/v1"
    assert p.model == "auto"
    assert p.is_available() is True

    # Check key masking
    masked = p.masked_key
    assert dummy_key not in masked
    assert masked.endswith("7890")
    assert "..." in masked or "****" in masked

    # to_dict must never contain the raw key
    d = p.to_dict()
    assert dummy_key not in json.dumps(d)
    assert d["masked_key"] == masked
    assert d["configured"] is True


def test_freellmapi_empty_key_unavailable():
    """Provider without key or with blank key reports unavailable."""
    p = FreeLLMAPIProvider(api_key="", base_url="http://localhost:3001/v1")
    assert p.is_available() is False
    assert p.masked_key == ""
    d = p.to_dict()
    assert d["configured"] is False


# ─────────────────────────────────────────────────────────────────────────────
# 2. Dynamic Model Catalog Discovery & TTL Caching
# ─────────────────────────────────────────────────────────────────────────────

def test_freellmapi_list_models_dynamic_and_caching(monkeypatch):
    """Verify dynamic discovery from /v1/models with 60s TTL caching and auto-priority."""
    mock_get = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {"id": "claude-3-5-sonnet"},
            {"id": "gpt-4o"},
            {"id": "deepseek-coder"},
        ]
    }
    mock_get.return_value = mock_resp
    monkeypatch.setattr("ai.providers.freellmapi_provider.requests.get", mock_get)

    p = FreeLLMAPIProvider(api_key="test_key", base_url="http://localhost:3001/v1")
    models = p.list_models()

    assert mock_get.call_count == 1
    # 'auto' should be injected at the front
    assert models[0] == "auto"
    assert "gpt-4o" in models
    assert "claude-3-5-sonnet" in models

    # Second call within TTL should return cached result without calling requests.get again
    models_cached = p.list_models()
    assert mock_get.call_count == 1
    assert models_cached == models

    # Expiring the cache should trigger a new GET request
    p._models_cache = (time.monotonic() - 65, p._models_cache[1])
    p.list_models()
    assert mock_get.call_count == 2


def test_freellmapi_list_models_offline_fallback(monkeypatch):
    """When gateway network request fails, fall back gracefully to default list."""
    monkeypatch.setattr(
        "ai.providers.freellmapi_provider.requests.get",
        MagicMock(side_effect=Exception("Gateway unreachable")),
    )

    p = FreeLLMAPIProvider(api_key="test_key", base_url="http://localhost:3001/v1")
    models = p.list_models()
    assert "auto" in models
    assert len(models) >= 5
    assert "gpt-4o" in models


# ─────────────────────────────────────────────────────────────────────────────
# 3. Tool Calling: Native OpenAI Schema & Text Fallback Parsing
# ─────────────────────────────────────────────────────────────────────────────

def test_freellmapi_generate_native_tool_call(monkeypatch):
    """Verify native OpenAI tool_calls structure parsing."""
    tool_call_obj = {
        "id": "call_inspect_123",
        "type": "function",
        "function": {
            "name": "get_running_apps_processes",
            "arguments": "{\"limit\": 10}",
        },
    }
    mock_get = MagicMock(return_value=MagicMock(status_code=200))
    mock_post = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Checking active system processes...",
                    "tool_calls": [tool_call_obj],
                }
            }
        ]
    }
    mock_post.return_value = mock_resp
    monkeypatch.setattr("ai.providers.freellmapi_provider.requests.get", mock_get)
    monkeypatch.setattr("ai.providers.freellmapi_provider.requests.post", mock_post)

    p = FreeLLMAPIProvider(api_key="test_key", base_url="http://localhost:3001/v1")
    result = p.generate(
        messages=[{"role": "user", "content": "What is running on my PC?"}],
        tools=[{"type": "function", "function": {"name": "get_running_apps_processes"}}],
    )

    assert result["provider"] == "freellmapi"
    assert result["text"] == "Checking active system processes..."
    assert len(result["tool_calls"]) == 1
    tc = result["tool_calls"][0]
    assert tc["name"] == "get_running_apps_processes"
    assert tc["args"] == {"limit": 10}
    assert result["assistant_message"]["tool_calls"][0]["function"]["name"] == "get_running_apps_processes"


def test_freellmapi_fallback_tool_parsing_xml_tags():
    """Verify fallback parser parses XML <tool_call> tags when model emits text."""
    p = FreeLLMAPIProvider(api_key="test_key", base_url="http://localhost:3001/v1")
    raw_text = """Let me inspect the screen for you.
<tool_call>
{"name": "inspect_screen", "arguments": {"check_errors": true}}
</tool_call>
I will analyze the result next."""

    calls = p.parse_fallback_tool_calls(raw_text)
    assert len(calls) == 1
    call = calls[0]
    assert call["name"] == "inspect_screen"
    assert call["args"] == {"check_errors": True}


def test_freellmapi_fallback_tool_parsing_json_fence():
    """Verify fallback parser parses markdown json code blocks."""
    p = FreeLLMAPIProvider(api_key="test_key", base_url="http://localhost:3001/v1")
    raw_text = """I will run system diagnostics.
```json
{
  "name": "diagnose_system_status",
  "arguments": {}
}
```
"""
    calls = p.parse_fallback_tool_calls(raw_text)
    assert len(calls) == 1
    assert calls[0]["name"] == "diagnose_system_status"
    assert calls[0]["args"] == {}


# ─────────────────────────────────────────────────────────────────────────────
# 4. SSE Streaming Generation
# ─────────────────────────────────────────────────────────────────────────────

def test_freellmapi_stream_generate(monkeypatch):
    """Verify stream_generate yields chunks from SSE stream."""
    sse_data = [
        b"data: {\"choices\": [{\"delta\": {\"content\": \"Hello\"}}]}\n\n",
        b"data: {\"choices\": [{\"delta\": {\"content\": \" world!\"}}]}\n\n",
        b"data: [DONE]\n\n",
    ]
    mock_get = MagicMock(return_value=MagicMock(status_code=200))
    mock_post = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.iter_lines.return_value = sse_data
    mock_post.return_value = mock_resp
    monkeypatch.setattr("ai.providers.freellmapi_provider.requests.get", mock_get)
    monkeypatch.setattr("ai.providers.freellmapi_provider.requests.post", mock_post)

    p = FreeLLMAPIProvider(api_key="test_key", base_url="http://localhost:3001/v1")
    generator = p.stream_generate([{"role": "user", "content": "Hi"}])
    tokens = [chunk["token"] for chunk in generator if not chunk.get("done") and chunk.get("token")]
    assert tokens == ["Hello", " world!"]


# ─────────────────────────────────────────────────────────────────────────────
# 5. Developer CLI Bridge & Agent Environment Injection
# ─────────────────────────────────────────────────────────────────────────────

def test_developer_cli_bridge_environment_injection(monkeypatch):
    """Verify runtime environment injection provides correct protocols without writing to disk."""
    monkeypatch.setenv("FREELLMAPI_API_KEY", "test_cli_secret_key")
    monkeypatch.setenv("FREELLMAPI_BASE_URL", "http://localhost:3001/v1")

    bridge = DeveloperCliBridge()
    cfg = bridge.get_freellmapi_config()
    assert cfg["configured"] is True
    # Ensure raw secret is not in the config dictionary
    assert "test_cli_secret_key" not in json.dumps(cfg)

    # Test Claude (Anthropic protocol)
    claude_env = bridge.get_agent_env("claude")
    assert claude_env.get("ANTHROPIC_BASE_URL") == "http://localhost:3001"
    assert claude_env.get("ANTHROPIC_AUTH_TOKEN") == "test_cli_secret_key"

    # Test Codex / Hermes / Aider / OpenCode / Cline / Antigravity (OpenAI protocol)
    for agent in ["codex", "hermes", "aider", "opencode", "cline", "agy", "antigravity"]:
        env = bridge.get_agent_env(agent)
        assert env.get("OPENAI_BASE_URL") == "http://localhost:3001/v1"
        assert env.get("OPENAI_API_KEY") == "test_cli_secret_key"


def test_developer_cli_bridge_detection():
    """Verify detect_clis returns genuine information and FreeLLMAPI readiness."""
    clis = developer_cli_bridge.detect_clis()
    assert "freellmapi" in clis
    assert "claude" in clis
    assert "codex" in clis
    assert "hermes" in clis
    assert "aider" in clis
    assert "opencode" in clis
    assert "antigravity" in clis
    assert "agy" in clis
    assert "cline" in clis

    # All installed CLIs should have their protocol defined
    assert clis["claude"]["freellmapi_protocol"] == "anthropic"
    assert clis["codex"]["freellmapi_protocol"] == "openai"


def test_developer_cli_bridge_pin_gating():
    """Verify read-only vs mutating PIN gating rules."""
    bridge = DeveloperCliBridge()

    # Read-only diagnostics should execute without a PIN and return structured diagnostics
    diag = bridge.diagnose_system()
    assert isinstance(diag, dict)
    assert "services" in diag
    assert "audio" in diag
    assert "git" in diag
    assert "clis" in diag
    assert "freellmapi" in diag["clis"]

    # Mutating action without PIN must be rejected
    res_no_pin = bridge.execute_remediation(action="remediate_service", pin="")
    assert res_no_pin["status"] == "error"
    assert "PIN" in res_no_pin["error"] or "Authorization denied" in res_no_pin["error"]

    # Mutating action with bad PIN must be rejected
    res_bad_pin = bridge.execute_remediation(action="remediate_service", pin="0000")
    assert res_bad_pin["status"] == "error"
    assert "Invalid PIN" in res_bad_pin["error"] or "Authorization denied" in res_bad_pin["error"]


# ─────────────────────────────────────────────────────────────────────────────
# 6. Registered Read-Only PC & Developer Tools
# ─────────────────────────────────────────────────────────────────────────────

def test_registered_pc_and_developer_tools():
    """Verify read-only inspection tools are registered in ToolRegistry."""
    registry = ToolRegistry()

    assert "get_running_apps_processes" in registry._tools
    assert "inspect_screen" in registry._tools
    assert "diagnose_system_status" in registry._tools

    # Test direct execution of running_apps_processes (alias or direct)
    res_procs = registry.execute("get_running_apps_processes", limit=5)
    assert res_procs.get("success") is True
    assert "Running Software" in str(res_procs.get("result", ""))

    # Test direct execution of inspect_screen
    res_screen = registry.execute("inspect_screen")
    assert res_screen.get("success") is True
    assert "Screen" in str(res_screen.get("result", "")) or "Display" in str(res_screen.get("result", ""))

    # Test direct execution of diagnose_system_status
    res_diag = registry.execute("diagnose_system_status")
    assert res_diag.get("success") is True
    assert "Developer" in str(res_diag.get("result", "")) or "FreeLLMAPI" in str(res_diag.get("result", ""))
