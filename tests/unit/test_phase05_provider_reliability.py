from unittest.mock import MagicMock

from ai.brain import JARVISBrain
from ai.providers.base import AIProvider


class _Provider(AIProvider):
    def __init__(self, name, model="m", available=True, responses=None):
        self.name = name
        self.model = model
        self.enabled = True
        self._available = available
        self._responses = list(responses or [{"text": "ok", "tool_calls": [], "provider": name, "model": model}])
        self.calls = 0

    def is_available(self):
        return self._available

    def generate(self, messages, tools=None, system=None, **kwargs):
        self.calls += 1
        idx = min(self.calls - 1, len(self._responses) - 1)
        result = dict(self._responses[idx])
        result.setdefault("provider", self.name)
        result.setdefault("model", self.model)
        return result


def _brain_with(providers):
    brain = object.__new__(JARVISBrain)
    brain._providers = providers
    brain._active = providers[0] if providers else None
    brain._sessions = {}
    brain._session_locks = {}
    brain._locks_mutex = __import__("threading").Lock()
    brain._cancelled_requests = set()
    brain._executor = MagicMock()
    brain.is_cancelled = lambda identifier: False
    brain._get_session_lock = lambda sid: __import__("threading").RLock()
    brain._get_session_history = lambda sid: []
    return brain


def test_no_implicit_fallback_without_explicit_authorization(monkeypatch):
    primary = _Provider("primary", responses=[{"text": "", "tool_calls": [], "error": "network unavailable"}])
    secondary = _Provider("secondary", responses=[{"text": "fallback answer", "tool_calls": []}])
    brain = _brain_with([primary, secondary])

    monkeypatch.setattr("memory.long_term.database.db.save_message", lambda *a, **k: None)
    monkeypatch.setattr("memory.long_term.database.db.get_session_messages", lambda *a, **k: [])

    result = brain.chat("hello", use_tools=False)

    assert result["provider"] == "primary"
    assert "error" in result
    assert secondary.calls == 0
    assert result.get("fallback_attempted") is False or result.get("fallback_attempted") is None
    assert result.get("failure_telemetry")


def test_authorized_fallback_switches_only_when_explicitly_allowed(monkeypatch):
    primary = _Provider("primary", responses=[{"text": "", "tool_calls": [], "error": "temporary upstream failure"}])
    secondary = _Provider("secondary", responses=[{"text": "fallback answer", "tool_calls": []}])
    brain = _brain_with([primary, secondary])

    monkeypatch.setattr("memory.long_term.database.db.save_message", lambda *a, **k: None)
    monkeypatch.setattr("memory.long_term.database.db.get_session_messages", lambda *a, **k: [])

    result = brain.chat("hello", use_tools=False, allow_fallback=True, max_provider_retries=0)

    assert result["provider"] == "secondary"
    assert result["response"] == "fallback answer"
    assert "error" not in result
    assert primary.calls == 1
    assert secondary.calls == 1
    assert result.get("failure_telemetry")


def test_retry_limit_is_bounded_before_failure(monkeypatch):
    primary = _Provider(
        "primary",
        responses=[
            {"text": "", "tool_calls": [], "error": "timeout"},
            {"text": "", "tool_calls": [], "error": "timeout"},
            {"text": "", "tool_calls": [], "error": "timeout"},
        ],
    )
    brain = _brain_with([primary])

    monkeypatch.setattr("memory.long_term.database.db.save_message", lambda *a, **k: None)
    monkeypatch.setattr("memory.long_term.database.db.get_session_messages", lambda *a, **k: [])

    result = brain.chat("hello", use_tools=False, max_provider_retries=2)

    assert result["provider"] == "primary"
    assert "error" in result
    assert primary.calls == 3  # initial + 2 retries
    assert len(result.get("failure_telemetry", [])) == 3


def test_explicit_provider_never_falls_back_even_if_authorized(monkeypatch):
    primary = _Provider("primary", responses=[{"text": "", "tool_calls": [], "error": "quota exceeded"}])
    secondary = _Provider("secondary", responses=[{"text": "fallback answer", "tool_calls": []}])
    brain = _brain_with([primary, secondary])

    monkeypatch.setattr("memory.long_term.database.db.save_message", lambda *a, **k: None)
    monkeypatch.setattr("memory.long_term.database.db.get_session_messages", lambda *a, **k: [])

    result = brain.chat("hello", use_tools=False, provider_name="primary", allow_fallback=True)

    assert result["provider"] == "primary"
    assert "error" in result
    assert secondary.calls == 0


def test_empty_response_is_not_claimed_as_success(monkeypatch):
    primary = _Provider("primary", responses=[{"text": "   ", "tool_calls": []}])
    brain = _brain_with([primary])

    monkeypatch.setattr("memory.long_term.database.db.save_message", lambda *a, **k: None)
    monkeypatch.setattr("memory.long_term.database.db.get_session_messages", lambda *a, **k: [])

    result = brain.chat("hello", use_tools=False)

    assert "could not be verified" in result["response"].lower() or "no answer" in result["response"].lower()
    assert result["provider"] == "primary"


def test_malformed_tool_call_payload_is_rejected(monkeypatch):
    primary = _Provider(
        "primary",
        responses=[{"text": "", "tool_calls": [{"name": "", "args": "bad"}]}],
    )
    brain = _brain_with([primary])

    monkeypatch.setattr("memory.long_term.database.db.save_message", lambda *a, **k: None)
    monkeypatch.setattr("memory.long_term.database.db.get_session_messages", lambda *a, **k: [])

    result = brain.chat("do tool", use_tools=True)

    assert "error" in result
    assert result["provider"] == "primary"
    assert primary.calls == 1
