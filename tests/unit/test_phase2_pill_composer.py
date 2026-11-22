import pytest
from unittest.mock import MagicMock, patch
from apps.api.chat_api import ChatRequest
from apps.voice.daemon_control import ALLOWED_ACTIONS


def test_chat_request_thinking_mode():
    req = ChatRequest(message="test message", thinking_mode=True)
    assert req.thinking_mode is True

    req_default = ChatRequest(message="test message")
    assert req_default.thinking_mode is False


def test_daemon_control_allows_dictate_actions():
    assert "dictate" in ALLOWED_ACTIONS
    assert "dictate_stop" in ALLOWED_ACTIONS


def test_voice_service_process_command_dedup_flags():
    from apps.voice.service import voice_service

    with patch("apps.voice.service.broadcast_chat_message", create=True) as mock_broadcast:
        with patch.object(voice_service, "speak_response") as mock_speak:
            with patch("ai.brain.get_brain") as mock_get_brain:
                mock_brain = MagicMock()
                mock_brain.chat.return_value = {"response": "Hello operator", "status": "ok"}
                mock_get_brain.return_value = mock_brain

                res = voice_service.process_command(
                    "hello",
                    speak=False,
                    turn_id="turn_test_123",
                    broadcast_user=False,
                    broadcast_assistant=False,
                )
                assert res == "Hello operator"
                assert mock_speak.call_count == 0


def test_brain_chat_thinking_mode_prefix():
    from ai.brain import JARVISBrain
    brain = JARVISBrain()

    with patch("tools.identity.permission_manager.permission_manager.check_chat_elevation_attempt") as mock_check:
        mock_check.return_value = "Elevation check simulated"
        res = brain.chat("Analyze quantum entanglement", thinking_mode=True, use_tools=False)
        assert res is not None
        mock_check.assert_called_once()
        passed_arg = mock_check.call_args[0][0]
        assert "[Thinking Mode: Enabled" in passed_arg
