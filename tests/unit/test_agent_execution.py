"""Isolated agent regressions: no network, device capture, or real tool actions."""
import copy
import json
from unittest.mock import MagicMock

import pytest

from ai.brain import JARVISBrain, MAX_TOOL_ROUNDS
from ai.providers.base import OpenAIProvider
from ai.tools.agent_tools import available_tools, execute_agent_tool
from tools.registry import ToolRegistry


@pytest.fixture
def registry(monkeypatch):
    registry = ToolRegistry(auto_register_core=False)
    registry.register_tool({"name": "probe", "description": "Read a test value", "schema": {"value": "str"},
                            "risk_level": 0, "permissions": [], "execute": lambda value: value})
    monkeypatch.setattr("tools.registry.tool_registry", registry)
    monkeypatch.setattr("tools.identity.permission_manager.permission_manager.check_tool_permission",
                        lambda *args, **kwargs: (True, "allowed"))
    monkeypatch.setattr(registry, "permission_check", lambda *a, **k: (True, None))
    monkeypatch.setattr(registry, "safety_check", lambda *a, **k: (True, None))
    return registry


@pytest.fixture
def brain(monkeypatch, registry):
    monkeypatch.setattr(JARVISBrain, "_init_providers", lambda self: None)
    monkeypatch.setattr("ai.brain.db", MagicMock())
    monkeypatch.setattr("ai.local_engine.LocalIntelligenceEngine.classify_intent", lambda *a: ("general", {}))
    monkeypatch.setattr("ai.brain.CompoundTaskOrchestrator.is_compound_request", lambda *a: False)
    brain = JARVISBrain()
    brain._sessions["default"] = []
    return brain


def provider_with(*responses):
    provider = MagicMock(name="provider")
    provider.name = "test"
    provider.model = "test-model"
    provider.is_available.return_value = True
    provider.generate.side_effect = list(responses)
    return provider


def call_result():
    return {"text": "", "tool_calls": [{"id": "call1", "name": "probe", "args": {"value": "ok"}}]}


def test_native_function_request_and_response(monkeypatch):
    response = MagicMock(status_code=200)
    response.json.return_value = {"choices": [{"message": {"content": None, "tool_calls": [
        {"id": "call1", "function": {"name": "probe", "arguments": '{"value":"ok"}'}}]}}]}
    post = MagicMock(return_value=response)
    monkeypatch.setattr("ai.providers.base.requests.post", post)
    provider = OpenAIProvider(api_key="test-api-key")
    schemas = [{"name": "probe", "parameters": {"type": "object"}}]
    result = provider.generate([{"role": "user", "content": "probe"}], tools=schemas)
    assert post.call_args.kwargs["json"]["tools"] == [{"type": "function", "function": schemas[0]}]
    assert result["tool_calls"][0]["args"] == {"value": "ok"}
    assert result["text"] == ""


@pytest.mark.parametrize("arguments", ["[]", "null", "broken"])
def test_invalid_provider_arguments_are_errors(monkeypatch, arguments):
    response = MagicMock(status_code=200)
    response.json.return_value = {"choices": [{"message": {"tool_calls": [
        {"id": "bad", "function": {"name": "probe", "arguments": arguments}}]}}]}
    monkeypatch.setattr("ai.providers.base.requests.post", lambda *a, **k: response)
    assert OpenAIProvider(api_key="test-api-key").generate([]).get("error")


def test_registry_schemas_and_untrusted_arguments(registry):
    assert available_tools("ADMIN")[0]["parameters"]["required"] == ["value"]
    for name, args in [("missing", {}), ("probe", []), ("probe", {"confirmed": True}), ("probe", {"value": 5})]:
        result = json.loads(execute_agent_tool(name, args, {"probe"}, "ADMIN"))
        assert result.get("error") or result.get("success") is False
    assert json.loads(execute_agent_tool("probe", {"value": "ok"}, {"probe"}, "ADMIN"))["result"] == "ok"


def test_role_rechecked_at_execution(registry, monkeypatch):
    monkeypatch.setattr("tools.identity.permission_manager.permission_manager.check_tool_permission",
                        lambda *a, **k: (False, "denied"))
    assert available_tools("GUEST") == []
    assert json.loads(execute_agent_tool("probe", {"value": "ok"}, {"probe"}, "GUEST"))["error"] == "denied"


def test_round_trip_preserves_call_ids(brain):
    provider = provider_with(call_result(), {"text": "Verified ok"})
    brain._providers = [provider]
    requests = []
    responses = iter([call_result(), {"text": "Verified ok"}])
    def generate(**kwargs):
        requests.append(copy.deepcopy(kwargs))
        return next(responses)
    provider.generate.side_effect = generate
    result = brain.chat("Please inspect this", role="ADMIN")
    assert result["response"] == "Verified ok"
    assert requests[1]["messages"][-2]["tool_calls"][0]["id"] == "call1"
    assert requests[1]["messages"][-1]["tool_call_id"] == "call1"
    assert len(result["tools_used"]) == 1


def test_provider_failover_retries_instead_of_claiming_success(brain):
    first = provider_with({"error": "unavailable"})
    second = provider_with({"text": "Recovered"})
    second.name = "second"
    brain._providers = [first, second]
    assert brain.chat("Please inspect this", role="ADMIN", allow_fallback=True)["response"] == "Recovered"
    second.generate.assert_called_once()


def test_execution_budget_reports_incomplete(brain):
    brain._providers = [provider_with(*[call_result() for _ in range(MAX_TOOL_ROUNDS)])]
    result = brain.chat("Please inspect this", role="ADMIN")
    assert result["error"] == "execution_limit"
    assert "not been verified" in result["response"]


def test_tools_disabled_blocks_model_calls(brain):
    brain._providers = [provider_with(call_result())]
    result = brain.chat("Please inspect this", role="ADMIN", use_tools=False)
    assert "disabled" in result["error"]
    assert result['status'] == 'failed'
    assert result["tools_used"] == []


def test_stream_routes_agent_request_to_shared_loop(brain, monkeypatch):
    chat = MagicMock(return_value={"response": "Verified", "tools_used": [{"tool": "probe"}]})
    monkeypatch.setattr(brain, "chat", chat)
    events = list(brain.stream_chat("Please inspect", provider_name="chosen", model_name="model"))
    assert [event["type"] for event in events] == ["start", "token", "done"]
    assert events[-1]["tools_used"] == [{"tool": "probe"}]
    assert chat.call_args.kwargs["provider_name"] == "chosen"


def test_text_only_skips_deterministic_actions(brain, monkeypatch):
    monkeypatch.setattr("ai.local_engine.LocalIntelligenceEngine.classify_intent", lambda *a: ("system_status", {}))
    respond = MagicMock(side_effect=AssertionError("No action allowed"))
    monkeypatch.setattr("ai.local_engine.LocalIntelligenceEngine.respond", respond)
    brain._providers = [provider_with({"text": "Explanation only"})]
    assert brain.chat("Explain system status", role="ADMIN", use_tools=False)["response"] == "Explanation only"
    respond.assert_not_called()


def test_registry_failure_never_uses_legacy_executor(registry, monkeypatch):
    monkeypatch.setattr(registry, "execute_tool", MagicMock(side_effect=RuntimeError("failure")))
    assert "no fallback" in json.loads(execute_agent_tool("probe", {"value": "ok"}, {"probe"}, "ADMIN"))["error"]


def test_stream_keeps_request_correlation(brain):
    brain._providers = [provider_with({"text": "Done"})]
    events = list(brain.stream_chat("Inspect this"))
    assert events[0]["request_id"] == events[-1]["request_id"]
    assert events[0]["message_id"] == events[-1]["message_id"]


def test_all_failed_providers_stop_without_cycles(brain):
    first = provider_with({"error": "first unavailable"})
    second = provider_with({"error": "second unavailable"})
    second.name = "second"
    brain._providers = [first, second]
    result = brain.chat("Inspect this", role="ADMIN", allow_fallback=True)
    assert result["error"] == "second unavailable"
    assert first.generate.call_count == second.generate.call_count == 1


def test_admin_role_alone_does_not_authorize_provider_fallback(brain):
    first = provider_with({'error':'unavailable'})
    second = provider_with({'text':'other provider answer'})
    second.name = 'second'
    brain._providers = [first, second]
    result = brain.chat('Inspect this', role='ADMIN')
    assert result.get('error')
    second.generate.assert_not_called()


def test_brain_uses_pin_gated_authorization_role(brain, monkeypatch):
    from types import SimpleNamespace
    session = SimpleNamespace(role='ADMIN', user_id='test-admin', authorization_role=lambda: 'USER')
    monkeypatch.setattr('apps.voice.session_manager.voice_session_mgr.get_active_session', lambda: session)
    available = MagicMock(return_value=[])
    monkeypatch.setattr('ai.tools.agent_tools.available_tools', available)
    brain._providers = [provider_with({'text': 'Done'})]
    brain.chat('Inspect this')
    available.assert_called_once_with('USER')
