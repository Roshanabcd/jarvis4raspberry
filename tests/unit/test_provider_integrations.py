import asyncio
import copy
import os
from unittest.mock import MagicMock

import pytest
from fastapi import BackgroundTasks, FastAPI
from fastapi.testclient import TestClient

from ai.providers.base import GeminiProvider, OpenAIProvider, OpenRouterProvider
from ai.providers.credentials import resolve_key, usable_key
from ai.providers.diagnostics import probe_provider
from config.config_manager import ConfigManager


@pytest.mark.parametrize('value', ['', 'sk-REPLACE_ME', 'your-google-key', 'sk-abcd****xyz', None])
def test_unusable_credentials_are_not_sent(value):
    assert not usable_key(value)


def test_real_gemini_key_wins_over_google_placeholder(monkeypatch):
    monkeypatch.setenv('GOOGLE_API_KEY', 'your-google-key')
    monkeypatch.setenv('GEMINI_API_KEY', 'test-gemini-key')
    assert resolve_key('gemini', {}) == 'test-gemini-key'


def test_gemini_preserves_history_tools_and_signed_call_metadata(monkeypatch):
    call = {'id': 'call1', 'type': 'function', 'function': {'name': 'probe', 'arguments': '{}'},
            'extra_content': {'google': {'thought_signature': 'opaque-signature'}}}
    message = {'role': 'assistant', 'content': None, 'tool_calls': [call]}
    response = MagicMock(status_code=200)
    response.json.return_value = {'choices': [{'message': message}]}
    post = MagicMock(return_value=response)
    monkeypatch.setattr('ai.providers.base.requests.post', post)
    history = [{'role': 'user', 'content': 'Earlier', 'timestamp': 123}, {'role': 'assistant', 'content': 'Reply'},
               {'role': 'user', 'content': 'Now inspect'}]
    schema = {'name': 'probe', 'parameters': {'type': 'object'}}
    result = GeminiProvider(api_key='test-gemini-key').generate(history, tools=[schema], system='System')
    payload = post.call_args.kwargs['json']
    assert payload['messages'] == [{'role': 'system', 'content': 'System'}] + [
        {k: v for k, v in item.items() if k != 'timestamp'} for item in history]
    assert payload['tools'][0]['function'] == schema
    assert result['assistant_message']['tool_calls'] == [call]
    assert result['provider'] == 'gemini'
    assert '?' not in post.call_args.args[0]


def test_openrouter_endpoint_and_sanitized_failure(monkeypatch):
    response = MagicMock(status_code=401, text='secret-in-upstream-body')
    monkeypatch.setattr('ai.providers.base.requests.post', lambda *a, **k: response)
    provider = OpenRouterProvider(api_key='test-openrouter-key')
    assert provider.base_url == 'https://openrouter.ai/api/v1'
    result = probe_provider(provider)
    assert result['status'] == 'authentication_failed'
    assert 'secret' not in str(result)


def test_missing_key_diagnostic_never_calls_network(monkeypatch):
    post = MagicMock()
    monkeypatch.setattr('ai.providers.base.requests.post', post)
    assert probe_provider(OpenRouterProvider(api_key=''))['status'] == 'missing_key'
    post.assert_not_called()


def test_provider_status_does_not_treat_placeholder_as_configured(monkeypatch):
    from ai.brain import JARVISBrain
    brain = object.__new__(JARVISBrain)
    brain._active = None
    provider = OpenRouterProvider(api_key="sk-REPLACE_ME")
    brain._providers = [provider]
    monkeypatch.setattr(provider, "is_available", lambda: False)
    status = brain.get_providers_status()["providers"][0]
    assert status["credential_configured"] is False
    assert status["verification"] == "missing_key"


def test_atomic_environment_save_preserves_other_values_and_permissions(tmp_path):
    from dotenv import dotenv_values
    cfg_dir = tmp_path / 'config'
    cfg_dir.mkdir()
    env = tmp_path / '.env'
    env.write_text("EXISTING='keep me'\n")
    manager = object.__new__(ConfigManager)
    manager.config_dir = str(cfg_dir)
    assert manager.save_env({'OPENROUTER_API_KEY': 'test key # with spaces'})
    assert dotenv_values(env) == {'EXISTING': 'keep me', 'OPENROUTER_API_KEY': 'test key # with spaces'}
    assert env.stat().st_mode & 0o777 == 0o600
    before = env.read_bytes()
    assert not manager.save_env({'OPENAI_API_KEY': 'bad\nINJECTED=value'})
    assert env.read_bytes() == before


@pytest.fixture
def integration_client(monkeypatch):
    from apps.api import settings_api
    from apps.api.admin_action_policy import require_admin_action
    cfg = MagicMock()
    cfg.get.side_effect = lambda key, default=None: default
    cfg.save_env.return_value = True
    monkeypatch.setattr(settings_api, 'config', cfg)
    brain = MagicMock()
    monkeypatch.setattr('ai.brain.get_brain', lambda: brain)
    app = FastAPI()
    app.include_router(settings_api.settings_router, prefix='/api')
    app.dependency_overrides[require_admin_action] = lambda: None
    with TestClient(app) as client:
        yield client, cfg, brain


def test_masked_keys_do_not_overwrite_credentials(integration_client):
    client, cfg, brain = integration_client
    r = client.post('/api/settings/integrations', json={'settings': {'openai_api_key': 'sk-abcd****xyz'}})
    assert r.status_code == 200
    cfg.save_env.assert_not_called()
    brain.refresh_providers.assert_not_called()


def test_saved_key_refreshes_running_providers(integration_client, monkeypatch):
    client, cfg, brain = integration_client
    monkeypatch.setenv('OPENROUTER_API_KEY', 'old-test-key')
    r = client.post('/api/settings/integrations', json={'settings': {'openrouter_api_key': 'new-test-key'}})
    assert r.status_code == 200
    cfg.save_env.assert_called_once_with({'OPENROUTER_API_KEY': 'new-test-key'})
    assert os.environ['OPENROUTER_API_KEY'] == 'new-test-key'
    brain.refresh_providers.assert_called_once()


def test_failed_save_does_not_activate_key(integration_client, monkeypatch):
    client, cfg, brain = integration_client
    cfg.save_env.return_value = False
    monkeypatch.setenv('OPENROUTER_API_KEY', 'old-test-key')
    r = client.post('/api/settings/integrations', json={'settings': {'openrouter_api_key': 'new-test-key'}})
    assert r.status_code == 500
    assert os.environ['OPENROUTER_API_KEY'] == 'old-test-key'
    brain.refresh_providers.assert_not_called()


def test_provider_probe_requires_explicit_admin_action():
    from apps.api.chat_api import chat_router
    app = FastAPI()
    app.include_router(chat_router, prefix='/api')
    with TestClient(app) as client:
        r = client.post('/api/chat/providers/test', json={'provider': 'openrouter'})
    assert r.status_code == 428


def test_voice_command_returns_before_synthesis(monkeypatch):
    from apps.api.voice_api import run_command, CommandRequest, voice_service
    process = MagicMock(return_value='Ready')
    speak = MagicMock()
    enqueue = MagicMock(return_value=MagicMock(job_id='job-test', status='queued'))
    monkeypatch.setattr(voice_service, 'process_command', process)
    monkeypatch.setattr(voice_service, 'speak_response', speak)
    monkeypatch.setattr(voice_service, 'enqueue_response', enqueue)
    background = BackgroundTasks()
    result = run_command(CommandRequest(text='hello'), background)
    assert result['response'] == 'Ready'
    process.assert_called_once_with('hello', speak=False)
    speak.assert_not_called()
    asyncio.run(background())
    speak.assert_not_called()
    enqueue.assert_called_once_with('Ready', broadcast=False)
    assert result['job_id'] == 'job-test'
    assert result['job_status'] == 'queued'


def test_refresh_preserves_selected_model_and_history(monkeypatch):
    from ai.brain import JARVISBrain
    brain = object.__new__(JARVISBrain)
    brain._active = OpenRouterProvider(api_key='old-test-key', model='chosen-model')
    brain._providers = [brain._active]
    brain._sessions = {'existing': [{'role': 'user', 'content': 'Earlier'}]}
    before = copy.deepcopy(brain._sessions)
    monkeypatch.setattr(JARVISBrain, '_init_providers', lambda self: self._providers.append(OpenRouterProvider(api_key='new-test-key')))
    brain.refresh_providers()
    assert brain._active.api_key == 'new-test-key'
    assert brain._active.model == 'chosen-model'
    assert brain._sessions == before


def test_ollama_honors_remaining_budget_for_large_model(monkeypatch):
    from ai.providers.base import OllamaProvider
    response = MagicMock(status_code=200)
    response.json.return_value = {'message': {'content': 'ok'}}
    post = MagicMock(return_value=response)
    monkeypatch.setattr('ai.providers.base.requests.post', post)
    provider = OllamaProvider(model='qwen3.5:4b')
    provider.generate([{'role': 'user', 'content': 'hello'}], request_timeout=7)
    assert post.call_args.kwargs['timeout'] == 7


def test_ollama_availability_reuses_short_cache(monkeypatch):
    from ai.providers.base import OllamaProvider
    response = MagicMock(status_code=200)
    response.json.return_value = {'models': [{'name': 'llama3.2:1b'}]}
    get = MagicMock(return_value=response)
    monkeypatch.setattr('ai.providers.base.requests.get', get)
    provider = OllamaProvider()
    assert provider.is_available()
    assert provider.is_available()
    get.assert_called_once()


def test_anthropic_native_tool_calling_and_result_continuation(monkeypatch):
    from ai.providers.base import AnthropicProvider
    # Round 1: Claude decides to invoke a tool
    mock_resp1 = MagicMock(status_code=200)
    mock_resp1.json.return_value = {
        "content": [
            {"type": "text", "text": "Checking status"},
            {"type": "tool_use", "id": "toolu_abc123", "name": "get_system_status", "input": {}}
        ],
        "usage": {"output_tokens": 15}
    }
    post = MagicMock(return_value=mock_resp1)
    monkeypatch.setattr("ai.providers.base.requests.post", post)

    provider = AnthropicProvider(api_key="sk-ant-test-key")
    schema = [{"name": "get_system_status", "description": "Get system status", "parameters": {"type": "object", "properties": {}}}]
    res1 = provider.generate([{"role": "user", "content": "What is system status?"}], tools=schema, system="You are JARVIS")

    # Verify tools payload formatted with input_schema
    payload1 = post.call_args.kwargs["json"]
    assert "tools" in payload1
    assert payload1["tools"][0]["name"] == "get_system_status"
    assert payload1["tools"][0]["input_schema"] == {"type": "object", "properties": {}}
    assert payload1["system"] == "You are JARVIS"

    # Verify tool calls parsed
    assert len(res1["tool_calls"]) == 1
    assert res1["tool_calls"][0]["name"] == "get_system_status"
    assert res1["tool_calls"][0]["id"] == "toolu_abc123"

    # Round 2: continuation with tool result
    mock_resp2 = MagicMock(status_code=200)
    mock_resp2.json.return_value = {
        "content": [{"type": "text", "text": "System status is healthy."}],
        "usage": {"output_tokens": 10}
    }
    post.return_value = mock_resp2

    continuation_messages = [
        {"role": "user", "content": "What is system status?"},
        res1["assistant_message"],
        {"role": "tool", "content": '{"cpu": "healthy"}', "tool_call_id": "toolu_abc123"}
    ]
    res2 = provider.generate(continuation_messages, tools=schema, system="You are JARVIS")
    payload2 = post.call_args.kwargs["json"]
    # Verify continuation messages conversion: tool result converted to role: user with tool_result block
    last_msg = payload2["messages"][-1]
    assert last_msg["role"] == "user"
    assert last_msg["content"][0]["type"] == "tool_result"
    assert last_msg["content"][0]["tool_use_id"] == "toolu_abc123"
    assert res2["text"] == "System status is healthy."


def test_configurable_model_ids_from_env(monkeypatch):
    from ai.providers.base import AnthropicProvider, GeminiProvider, NvidiaNimProvider, OpenRouterProvider
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-custom")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
    monkeypatch.setenv("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")
    monkeypatch.setenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

    p_ant = AnthropicProvider(api_key="sk-ant-test")
    assert p_ant.model == "claude-3-5-sonnet-custom"

    p_gem = GeminiProvider(api_key="test-key")
    assert p_gem.model == "gemini-2.0-flash-exp"

    p_nvd = NvidiaNimProvider(api_key="test-key")
    assert p_nvd.model == "meta/llama-3.3-70b-instruct"

    p_opr = OpenRouterProvider(api_key="test-key")
    assert p_opr.model == "anthropic/claude-3.5-sonnet"


def test_brain_never_silently_switches_provider_on_explicit_selection(monkeypatch):
    from ai.brain import JARVISBrain
    from ai.providers.base import OpenAIProvider, OllamaProvider

    brain = object.__new__(JARVISBrain)
    brain._sessions = {}
    p_oai = OpenAIProvider(api_key="sk-test-key", enabled=True)
    p_oll = OllamaProvider(enabled=True)
    brain._providers = [p_oai, p_oll]
    brain._active = p_oai

    monkeypatch.setattr(p_oai, "is_available", lambda: True)
    monkeypatch.setattr(p_oll, "is_available", lambda: True)
    monkeypatch.setattr(p_oai, "generate", lambda *a, **k: {"text": "", "tool_calls": [], "error": "Quota exceeded"})

    result = brain.chat("Hello", provider_name="openai", use_tools=False)
    # Must NOT switch to ollama silently!
    assert result.get("provider") == "openai" or "openai" in result.get("error", "").lower() or "error" in result.get("provider", "").lower()
    assert result.get("provider") != "ollama"
    assert "error" in result or result.get("response", "").startswith("⚠️")

