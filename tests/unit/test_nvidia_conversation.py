"""NVIDIA discovery and conversation streaming without accounts or real devices."""
from unittest.mock import MagicMock

import pytest

from ai.brain import JARVISBrain
from ai.providers.base import NvidiaNimProvider, OpenAIProvider, OllamaProvider
from ai.providers.diagnostics import probe_provider


def test_nvidia_catalog_validates_ids_and_caches_discovery(monkeypatch):
    provider = NvidiaNimProvider(api_key='synthetic-key', model='selected/model')
    response = MagicMock(status_code=200)
    response.json.return_value = {'data':[{'id':'new/chat-model'},{'id':'<script>'},{'id':None},{'id':'new/chat-model'}]}
    get = MagicMock(return_value=response)
    monkeypatch.setattr('ai.providers.base.requests.get', get)
    assert provider.list_models() == ['selected/model','new/chat-model']
    assert provider.list_models() == ['selected/model','new/chat-model']
    get.assert_called_once()
    assert get.call_args.kwargs['timeout'] == 5


def test_nvidia_missing_key_does_not_request_catalog(monkeypatch):
    provider = NvidiaNimProvider(api_key='sk-REPLACE_ME', model='selected')
    get = MagicMock()
    monkeypatch.setattr('ai.providers.base.requests.get', get)
    assert provider.list_models() == ['selected']
    get.assert_not_called()


def test_nvidia_retired_model_is_reported_as_unavailable(monkeypatch):
    provider = NvidiaNimProvider(api_key='synthetic-key')
    monkeypatch.setattr(provider, 'generate', lambda *a, **kw: {'error':'retired', 'http_status':410})
    assert probe_provider(provider)['status'] == 'model_or_endpoint_unavailable'


@pytest.mark.parametrize('provider', [OpenAIProvider(api_key='synthetic-key'), OllamaProvider()])
def test_closing_stream_closes_http_response(monkeypatch, provider):
    response = MagicMock(status_code=200)
    response.iter_lines.return_value = iter([
        b'data: {"choices":[{"delta":{"content":"first"}}]}' if provider.name != 'ollama'
        else b'{"message":{"content":"first"},"done":false}',
    ])
    post = MagicMock(return_value=response)
    monkeypatch.setattr('ai.providers.base.requests.post', post)
    stream = provider.stream_generate([], max_tokens=123)
    assert next(stream)['token'] == 'first'
    stream.close()
    response.close.assert_called_once()
    payload = post.call_args.kwargs['json']
    assert (payload['options']['num_predict'] if provider.name=='ollama' else payload['max_tokens']) == 123


@pytest.fixture
def brain(monkeypatch):
    monkeypatch.setattr(JARVISBrain, '_init_providers', lambda self: None)
    monkeypatch.setattr('ai.brain.db', MagicMock())
    monkeypatch.setattr('ai.local_engine.LocalIntelligenceEngine.classify_intent', lambda *a: ('general', {}))
    b = JARVISBrain()
    b._sessions['default'] = []
    return b


def test_conversation_streams_tokens_without_tools_and_cancels(brain, monkeypatch):
    provider = MagicMock()
    provider.name, provider.model = 'nvidia', 'chat-model'
    closed = []
    def stream(*a, **kw):
        try:
            yield {'token':'first'}
            yield {'token':'must not appear'}
        finally:
            closed.append(True)
    provider.stream_generate.side_effect = stream
    monkeypatch.setattr(brain, '_get_provider', lambda *a: provider)
    output = brain.stream_chat('Explain a topic',use_tools=False)
    start = next(output)
    assert start['type'] == 'start'
    assert next(output)['content'] == 'first'
    brain.cancel_request(start['request_id'])
    rest = list(output)
    assert rest[-1]['status'] == 'cancelled'
    assert 'must not appear' not in str(rest)
    assert closed == [True]
    provider.generate.assert_not_called()
    kwargs = provider.stream_generate.call_args.kwargs
    assert 'tools' not in kwargs
    assert kwargs['request_timeout'] == 20


def test_conversation_failure_does_not_expose_upstream_error(brain, monkeypatch):
    provider = MagicMock()
    provider.name, provider.model = 'nvidia', 'chat-model'
    provider.stream_generate.return_value = iter([{'error':'sensitive upstream content'}])
    monkeypatch.setattr(brain, '_get_provider', lambda *a: provider)
    events = list(brain.stream_chat('Explain a topic', use_tools=False))
    assert events[-1]['status'] == 'failed'
    assert 'sensitive upstream content' not in str(events)


def test_nvidia_environment_model_wins_over_legacy_configuration(monkeypatch):
    monkeypatch.setenv('NVIDIA_MODEL', 'nvidia/current-model')
    brain = object.__new__(JARVISBrain)
    brain._providers = []
    brain._init_providers()
    assert next(p for p in brain._providers if p.name=='nvidia').model == 'nvidia/current-model'


@pytest.mark.parametrize('ending', [b'', b'data: {"choices":[{"delta":{},"finish_reason":"length"}]}'])
def test_truncated_cloud_reply_is_not_reported_as_completed(monkeypatch, ending):
    provider = NvidiaNimProvider(api_key='synthetic-key')
    response = MagicMock(status_code=200)
    response.iter_lines.return_value = iter([b'data: {"choices":[{"delta":{"content":"Partial"}}]}', ending])
    monkeypatch.setattr('ai.providers.base.requests.post', lambda *a, **kw: response)
    events = list(provider.stream_generate([]))
    assert events[0]['token'] == 'Partial'
    assert events[-1]['error']
    response.close.assert_called_once()


def test_background_session_revoked_before_tool_dispatch(brain, monkeypatch):
    provider = MagicMock()
    provider.name, provider.model = 'nvidia', 'chat-model'
    provider.generate.return_value = {'tool_calls':[{'name':'calculate','args':{'expression':'17+25'}}]}
    monkeypatch.setattr(brain, '_get_provider', lambda *a: provider)
    monkeypatch.setattr('ai.tools.agent_tools.available_tools', lambda *a, **kw: [{'name':'calculate'}])
    executor = MagicMock()
    monkeypatch.setattr('ai.tools.agent_tools.execute_agent_tool', executor)
    guard = MagicMock(side_effect=[True, True, False])
    result = brain.chat('Please compute the answer', role='GUEST', _allow_compound=False, _authorization_check=guard)
    assert result['status'] == 'failed'
    executor.assert_not_called()


def test_background_expired_session_never_starts_inference(brain):
    result = brain.chat('Do a task', _authorization_check=lambda: False)
    assert result['error'] == 'authorization_changed'
