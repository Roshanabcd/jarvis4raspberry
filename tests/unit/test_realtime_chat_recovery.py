"""Real-time regressions without cloud requests, devices, or private user data."""
import threading
import time
from unittest.mock import MagicMock

import pytest
import requests
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ai.brain import JARVISBrain
from ai.conversation_responses import immediate_reply
from ai.providers.base import OllamaProvider, OpenRouterProvider


@pytest.fixture
def brain(monkeypatch):
    monkeypatch.setattr(JARVISBrain, '_init_providers', lambda self: None)
    monkeypatch.setattr('ai.brain.db', MagicMock())
    monkeypatch.setattr('ai.local_engine.LocalIntelligenceEngine.classify_intent', lambda *a: ('general', {}))
    monkeypatch.setattr('ai.brain.CompoundTaskOrchestrator.is_compound_request', lambda *a: False)
    monkeypatch.setattr('ai.tools.agent_tools.available_tools', lambda *a, **k: [])
    instance = JARVISBrain()
    instance._sessions['default'] = []
    return instance


def test_greeting_without_model_or_network(brain, monkeypatch):
    lookup = MagicMock(side_effect=AssertionError('greeting must not call a provider'))
    monkeypatch.setattr(brain, '_get_provider', lookup)
    result = brain.chat('hello!', provider_name='ollama')
    assert 'Hello' in result['response']
    assert result['tools_used'] == []
    assert result['model'] == 'local_conversation'
    lookup.assert_not_called()


@pytest.mark.parametrize('text', ['hello, delete my files', 'thanks, now open a browser',
                                  'explain what hello means', 'are you listening to my microphone?'])
def test_greeting_never_swallows_a_task(text):
    assert immediate_reply(text) is None


def test_heartbeat_and_disconnect_do_not_wait_for_model(brain, monkeypatch):
    release = threading.Event()
    monkeypatch.setattr('ai.brain.STREAM_HEARTBEAT_SECONDS', 0.01)
    def blocked_chat(*args, **kwargs):
        release.wait(2)
        return {'response':'finished'}
    monkeypatch.setattr(brain, 'chat', blocked_chat)
    stream = brain.stream_chat('slow request')
    try:
        start = next(stream)
        heartbeat = next(stream)
        assert heartbeat['type'] == 'progress'
        assert heartbeat['stage'] == 'waiting'
        before = time.monotonic()
        stream.close()
        assert time.monotonic() - before < 0.5
        assert brain.is_cancelled(start['request_id'])
    finally:
        release.set()


def test_cancel_during_inference_never_executes_returned_tools(brain, monkeypatch):
    provider = MagicMock()
    provider.name = 'test'
    provider.model = 'test'
    def generate(**kwargs):
        brain.cancel_request('request-test')
        return {'tool_calls':[{'name':'dangerous_tool', 'args':{}, 'id':'call'}]}
    provider.generate.side_effect = generate
    monkeypatch.setattr(brain, '_get_provider', lambda *a: provider)
    execute = MagicMock()
    monkeypatch.setattr('ai.tools.agent_tools.execute_agent_tool', execute)
    result = brain.chat('perform this task', _request_id='request-test')
    assert result['status'] == 'cancelled'
    execute.assert_not_called()


def test_local_timeout_is_bounded_and_user_answer_is_actionable(brain, monkeypatch):
    provider = MagicMock()
    provider.name = 'ollama'
    provider.model = 'local'
    provider.generate.return_value = {'error':'HTTPConnectionPool secret transport detail', 'text':''}
    monkeypatch.setattr(brain, '_get_provider', lambda *a: provider)
    result = brain.chat('explain recursion', provider_name='ollama')
    assert provider.generate.call_args.kwargs['request_timeout'] <= 20
    assert 'Integrations' in result['response']
    assert 'HTTPConnectionPool' not in result['response']


def test_local_timeout_cools_down_without_repeating_request(monkeypatch):
    provider = OllamaProvider()
    post = MagicMock(side_effect=requests.Timeout('synthetic timeout'))
    monkeypatch.setattr('ai.providers.base.requests.post', post)
    assert provider.generate([{'role':'user','content':'test'}]).get('error')
    result = provider.generate([{'role':'user','content':'test again'}])
    assert result['error'] == 'local_provider_cooling_down'
    post.assert_called_once()


def test_busy_local_model_does_not_queue_another_slow_request(monkeypatch):
    provider = OllamaProvider()
    post = MagicMock()
    monkeypatch.setattr('ai.providers.base.requests.post', post)
    provider._inference_slot.acquire()
    try:
        assert provider.generate([])['error'] == 'local_provider_busy'
        post.assert_not_called()
    finally:
        provider._inference_slot.release()


def test_free_route_is_available_without_overriding_selected_model(monkeypatch):
    monkeypatch.delenv('OPENROUTER_MODEL', raising=False)
    monkeypatch.setattr('ai.providers.base.config.get', lambda *a: {})
    assert OpenRouterProvider(api_key='').model == 'openrouter/free'
    provider = OpenRouterProvider(api_key='', model='user-selected-model')
    assert provider.model == 'user-selected-model'
    assert provider.list_models() == ['user-selected-model', 'openrouter/free']


def test_status_selects_configured_default_instead_of_first_installed_model(brain, monkeypatch):
    local, cloud = MagicMock(), MagicMock()
    local.name, cloud.name = 'ollama', 'openrouter'
    local.model, cloud.model = 'local', 'openrouter/free'
    local.is_available.return_value = cloud.is_available.return_value = True
    local.list_models.return_value, cloud.list_models.return_value = ['local'], ['openrouter/free']
    local.api_key = cloud.api_key = ''
    brain._providers = [local, cloud]
    monkeypatch.setattr('ai.brain.config.get', lambda key, default=None: 'openrouter' if key=='default_provider' else default)
    status = brain.get_providers_status()
    assert status['active_provider'] == 'openrouter'
    assert status['active_model'] == 'openrouter/free'


def test_provider_probe_leaves_room_for_reasoning_before_short_answer():
    from ai.providers.diagnostics import probe_provider
    provider = MagicMock()
    provider.name = 'openrouter'
    provider.model = 'openrouter/free'
    provider.api_key = 'synthetic-test-key'
    provider.generate.return_value = {'text':'JARVIS_OK'}
    assert probe_provider(provider)['status'] == 'passed'
    assert provider.generate.call_args.kwargs['max_tokens'] == 256


def test_failed_chat_is_not_spoken_and_stream_acknowledges_first(monkeypatch):
    from apps.api.chat_api import chat_router
    fake = MagicMock()
    fake.chat.return_value = {'response':'Provider unavailable', 'error':'timeout'}
    fake.stream_chat.return_value = iter([
        {'type':'token','content':'Provider unavailable'},
        {'type':'done','error':'timeout'},
    ])
    monkeypatch.setattr('ai.brain.get_brain', lambda: fake)
    speech = MagicMock()
    monkeypatch.setattr('apps.voice.speech_manager.speech_manager.synthesize_and_stage', speech)
    app = FastAPI()
    app.include_router(chat_router, prefix='/api')
    with TestClient(app) as client:
        assert client.post('/api/chat', json={'message':'question','speak':True}).status_code == 200
        stream = client.post('/api/chat/stream', json={'message':'question','speak':True}).text
    assert stream.index('accepted') < stream.index('token')
    assert '"type": "audio"' not in stream
    speech.assert_not_called()
