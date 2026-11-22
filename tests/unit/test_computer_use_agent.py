"""
Unit tests for JARVIS OS Phase 3:
Vision-guided desktop computer-use tools, streaming interruption fixes,
permission gating, and background operation.
"""

import json
import os
import time
from unittest.mock import MagicMock, patch

import pytest

from ai.brain import JARVISBrain
from tools.desktop.unified_computer_service import unified_computer_service
from tools.desktop.screen_intelligence import screen_intelligence
from tools.identity.permission_manager import permission_manager
from tools.identity.user_manager import UserRole
from tools.registry import tool_registry


@pytest.fixture(autouse=True)
def reset_active_user():
    permission_manager.set_active_user({
        "user_id": "operator",
        "display_name": "Roshan",
        "role": UserRole.USER.value,
    })
    yield
    permission_manager._current_user = None


class TestComputerUseToolRegistration:
    """Verifies that all Phase 3 tools are registered and permitted."""

    PHASE3_TOOLS = [
        "inspect_screen",
        "monitor_screen",
        "focus_window",
        "desktop_click",
        "desktop_type",
        "desktop_hotkey",
        "desktop_scroll",
        "browser_ui_action",
        "run_safe_terminal_task",
    ]

    def test_tools_registered_in_registry(self):
        for tool_name in self.PHASE3_TOOLS:
            assert tool_registry.has_tool(tool_name), f"Tool '{tool_name}' must be registered"
            tool = tool_registry.get_tool(tool_name)
            assert tool is not None
            assert callable(tool["execute"])
            assert isinstance(tool["risk_level"], int)

    def test_permission_gating_for_user_role(self):
        permission_manager.set_active_user({
            "user_id": "test_user",
            "display_name": "Test User",
            "role": UserRole.USER.value,
        })
        for tool_name in self.PHASE3_TOOLS:
            allowed, reason = permission_manager.check_tool_permission(tool_name, user_role=UserRole.USER.value)
            assert allowed is True, f"User role should have permission for {tool_name}: {reason}"

    def test_permission_gating_for_guest_role(self):
        # Guests can only observe/inspect screen, not click, type, or execute commands
        allowed_inspect, _ = permission_manager.check_tool_permission("inspect_screen", user_role=UserRole.GUEST.value)
        allowed_monitor, _ = permission_manager.check_tool_permission("monitor_screen", user_role=UserRole.GUEST.value)
        assert allowed_inspect is True
        assert allowed_monitor is True

        for mutating_tool in ["desktop_click", "desktop_type", "run_safe_terminal_task"]:
            allowed, reason = permission_manager.check_tool_permission(mutating_tool, user_role=UserRole.GUEST.value)
            assert allowed is False, f"Guest should not be permitted {mutating_tool}: {reason}"


class TestUnifiedComputerService:
    """Tests execution of desktop and browser operations."""

    def test_inspect_screen_returns_thumbnail_and_summary(self):
        with patch.object(screen_intelligence, "inspect_screen") as mock_inspect:
            mock_inspect.return_value = {
                "active_window": {"app": "Google Chrome", "title": "YouTube - Google Chrome"},
                "open_windows_count": 2,
                "has_error": False,
                "spoken_summary": "Active window is YouTube in Google Chrome. Screen is clear.",
                "response": "Screen inspection complete.",
                "thumbnail_url": "/api/desktop/thumbnail?t=123",
            }
            res = unified_computer_service.inspect_screen()
            assert res["active_window"]["app"] == "Google Chrome"
            assert res["has_error"] is False
            assert "spoken_summary" in res
            assert res["thumbnail_url"] == "/api/desktop/thumbnail?t=123"

    def test_browser_ui_action_switch_youtube_account_progress(self):
        progress_events = []

        def on_prog(event):
            progress_events.append(event)

        with patch("tools.desktop.native_backend.native_backend.focus_window", return_value={"verified": True}),              patch("tools.desktop.native_backend.native_backend.click", return_value={"verified": True}),              patch("tools.desktop.native_backend.native_backend.get_screen_resolution", return_value={"width": 1440, "height": 900}):
            res = unified_computer_service.browser_ui_action(
                action="switch_youtube_account",
                target="Work account",
                on_progress=on_prog,
            )
            # Click delivery cannot establish the selected website identity.
            assert res["status"] == "unverified"
            assert res["verified"] is False
            assert "not confirmed" in res["spoken_summary"]
            assert res["action"] == "switch_youtube_account"
            assert len(progress_events) == 3
            assert "[Step 1/3]" in progress_events[0]["detail"]
            assert "[Step 2/3]" in progress_events[1]["detail"]
            assert "[Step 3/3]" in progress_events[2]["detail"]
            assert "spoken_summary" in res
            assert "Google Chrome" in res["spoken_summary"]

    def test_run_safe_terminal_task_read_only_allowed(self):
        res = unified_computer_service.run_safe_terminal_task("echo 'JARVIS Phase 3 Test'")
        assert res["status"] == "ok"
        assert res["verified"] is True
        assert "JARVIS Phase 3 Test" in res["output"]

    def test_run_safe_terminal_task_mutating_requires_confirmation(self):
        res = unified_computer_service.run_safe_terminal_task("rm -rf /tmp/fake_dir")
        assert res["status"] == "confirmation_required"
        assert res["requires_confirmation"] is True
        assert res["verified"] is False


class TestBrainStreamNoInterruption:
    """Verifies that tool execution exceptions do not emit 'The reply was interrupted'."""

    def test_brain_stream_catches_tool_exception_gracefully(self):
        brain = JARVISBrain()

        def faulty_tool():
            raise RuntimeError("Intentional tool failure for testing")

        tool_registry.register_tool({
            "name": "faulty_test_tool",
            "description": "Faulty tool for test",
            "schema": {},
            "risk_level": 0,
            "permissions": ["test:read"],
            "execute": faulty_tool,
        })

        events = []
        for chunk in brain.stream_chat(
            message="run faulty_test_tool",
            role="USER",
            thinking_mode=False,
            user_id="operator",
        ):
            events.append(chunk)

        content_chunks = "".join(e.get("content", "") for e in events)
        assert "The reply was interrupted" not in content_chunks
        done_events = [e for e in events if e.get("type") == "done"]
        assert len(done_events) >= 1
