"""Tests for Phase 3 brain and task reliability enhancements.

Verifies:
- Explanatory questions do not accidentally trigger hardware fast paths
- Compound orchestrator preserves cohesive questions and splits operational tasks
- Tool relevance filtering for small local models
- Agent tool execution timeout and safety
- Stream progress events, correlation IDs, and cancellation
- Per-session concurrency serialization
"""
import json
import threading
import time
from unittest.mock import MagicMock

import pytest

from ai.brain import JARVISBrain
from ai.local_engine import LocalIntelligenceEngine
from ai.agents.task_orchestrator import CompoundTaskOrchestrator
from ai.tools.agent_tools import available_tools, execute_agent_tool
from tools.registry import ToolRegistry


class TestExplanatoryFastPathSafety:
    """Verifies explanatory queries route to AI brain rather than triggering hardware actions."""

    @pytest.fixture
    def engine(self):
        return LocalIntelligenceEngine()

    @pytest.mark.parametrize("query", [
        "How do robots move forward?",
        "Why do robots move forward?",
        "How can robots move forward?",
        "What is RAM?",
        "What is CPU?",
        "What is the difference between RAM and storage?",
        "Why do robots need sensors?",
        "Tell me about the history of artificial intelligence",
        "What does CPU stand for?",
        "Can you explain how a motor turns?",
        "Explain the concept of recursion",
    ])
    def test_explanatory_queries_route_to_general(self, engine, query):
        intent, _ = engine.classify_intent(query)
        assert intent == "general", f"Query '{query}' was misclassified as '{intent}' instead of 'general'"

    @pytest.mark.parametrize("query,expected_intent", [
        ("move forward", "robot_forward"),
        ("drive forward", "robot_forward"),
        ("system status", "system_status"),
        ("show cpu usage", "system_status"),
        ("calculate 2 + 2", "calculate"),
        ("emergency stop", "robot_estop"),
    ])
    def test_operational_commands_preserve_fastpath(self, engine, query, expected_intent):
        intent, _ = engine.classify_intent(query)
        assert intent == expected_intent, f"Command '{query}' expected '{expected_intent}', got '{intent}'"


class TestCompoundTaskSafety:
    """Verifies compound splitting only triggers for discrete multi-action requests."""

    @pytest.mark.parametrize("query", [
        "Explain how neural networks calculate weights, and tell me how they adjust gradients.",
        "What is the difference between RAM and storage, and why do computers need both?",
        "Can you explain how a computer calculates 2 + 2, and what is the difference between CPU and RAM?",
    ])
    def test_explanatory_questions_not_split(self, query):
        assert CompoundTaskOrchestrator.is_compound_request(query) is False

    @pytest.mark.parametrize("query", [
        "Tell me my current RAM usage, calculate 15 percent of 800, and write a short Python function that adds two numbers.",
        "Open YouTube, search for Hindi songs, play the first video, set its volume to 50 percent, and tell me the title",
    ])
    def test_multi_action_commands_are_split(self, query):
        assert CompoundTaskOrchestrator.is_compound_request(query) is True


class TestAgentToolsEnhancements:
    """Tests tool relevance filtering, timeouts, and authorization."""

    def test_local_model_relevance_filtering(self):
        # Admin gets filtered to top relevant tools when provider is local
        tools_full = available_tools("ADMIN")
        tools_filtered = available_tools(
            "ADMIN",
            query="calculate the sum of 10 and 20",
            provider_name="ollama",
            max_tools=5
        )
        assert len(tools_filtered) <= 5
        names = [t["name"] for t in tools_filtered]
        assert "calculate" in names

    def test_guest_role_is_strictly_filtered(self):
        guest_tools = available_tools("GUEST")
        guest_names = [t["name"] for t in guest_tools]
        assert "robot_move" not in guest_names
        assert "terminal_execute" not in guest_names

    def test_execute_agent_tool_timeout(self, monkeypatch):
        registry = ToolRegistry(auto_register_core=False)
        def slow_func(*args, **kwargs):
            time.sleep(1.0)
            return "done"
        registry.register_tool({
            "name": "slow_tool",
            "description": "Slow operation",
            "schema": {},
            "risk_level": 0,
            "permissions": [],
            "execute": slow_func,
        })
        monkeypatch.setattr("tools.registry.tool_registry", registry)
        monkeypatch.setattr("tools.identity.permission_manager.permission_manager.check_tool_permission",
                            lambda *a, **k: (True, "allowed"))
        res_json = execute_agent_tool("slow_tool", {}, {"slow_tool"}, "ADMIN", timeout=0.1)
        res = json.loads(res_json)
        assert "timed out" in res.get("error", "")


class TestBrainStreamingAndCancellation:
    """Tests incremental progress events, request cancellation, and concurrency control."""

    @pytest.fixture
    def mock_brain(self, monkeypatch):
        monkeypatch.setattr(JARVISBrain, "_init_providers", lambda self: None)
        monkeypatch.setattr("ai.brain.db", MagicMock())
        monkeypatch.setattr("ai.local_engine.LocalIntelligenceEngine.classify_intent", lambda *a: ("general", {}))
        monkeypatch.setattr("ai.brain.CompoundTaskOrchestrator.is_compound_request", lambda *a: False)
        brain = JARVISBrain()
        brain._sessions["test_session"] = []
        return brain

    def test_stream_emits_progress_events(self, mock_brain):
        provider = MagicMock()
        provider.name = "test_provider"
        provider.model = "test_model"
        provider.is_available.return_value = True

        call_result = {"text": "", "tool_calls": [{"id": "c1", "name": "calculate", "args": {"expression": "2+2"}}]}
        final_result = {"text": "The answer is 4", "tool_calls": []}
        provider.generate.side_effect = [call_result, final_result]

        mock_brain._providers = [provider]

        events = list(mock_brain.stream_chat("calculate 2+2", session_id="test_session"))
        event_types = [e["type"] for e in events]

        assert "start" in event_types
        assert "progress" in event_types
        assert "token" in event_types
        assert "done" in event_types

        progress_events = [e for e in events if e["type"] == "progress"]
        stages = [p["stage"] for p in progress_events]
        assert "model_inferring" in stages
        assert "tool_executing" in stages

        # Check correlation IDs
        req_id = events[0]["request_id"]
        for evt in events:
            assert evt["request_id"] == req_id

    def test_request_cancellation(self, mock_brain):
        assert mock_brain.cancel_request("req_test123") is True
        assert mock_brain.is_cancelled("req_test123") is True
        assert mock_brain.is_cancelled("other_req") is False

        # Cancelled request chat returns cancelled status immediately
        res = mock_brain.chat("Test message", session_id="test_session", _request_id="req_test123")
        assert res.get("status") == "cancelled"
        assert "cancelled" in res.get("response", "").lower()

    def test_per_session_concurrency_lock(self, mock_brain):
        sid = "concurrency_session"
        lock = mock_brain._get_session_lock(sid)
        assert lock is mock_brain._get_session_lock(sid)
        assert lock is not mock_brain._get_session_lock("another_session")
