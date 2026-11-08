"""Phase 5 Test Suite — Real-Time Voice Conversation Loop, Barge-in, and Interruption."""
import os
import pytest
from fastapi.testclient import TestClient

from apps.core.main import app
from apps.voice.service import voice_service
from apps.voice.conversation import ConversationManager
from apps.voice.gradio_tts import gradio_cloner


class TestPhase5VoiceLoop:
    """Test suite verifying Phase 5 full-duplex conversation loop and barge-in."""

    def test_barge_in_interruption_stop(self):
        # Trigger stop_playback directly
        voice_service.stop_playback()
        # Verify no error raised and cloner current player is stopped
        assert gradio_cloner._current_player is None

    def test_api_interrupt_endpoint(self):
        client = TestClient(app)
        res = client.post("/api/voice/interrupt")
        assert res.status_code == 200
        assert res.json() == {"status": "ok", "interrupted": True}

    def test_conversation_manager_dialogue_flow(self, tmp_path):
        cm = ConversationManager(timeout_seconds=60, storage_dir=str(tmp_path))
        sess = cm.start_session("loop_session")
        assert sess == "loop_session"
        assert cm.is_session_active() is True

        cm.add_turn("user", "Hello Jarvis, how are you?")
        cm.add_turn("assistant", "I am fully operational, sir.")

        ctx = cm.get_context()
        assert len(ctx) == 2
        assert ctx[0]["role"] == "user"
        assert ctx[1]["role"] == "assistant"

        cm.end_session()
        assert cm.is_session_active() is False
        assert os.path.exists(tmp_path / "loop_session.json")

    def test_process_command_e2e_voice_loop(self):
        # Process command end-to-end
        reply = voice_service.process_command("what is your name")
        assert reply is not None
        assert len(reply) > 0
        # Check turn recorded in conversation manager
        ctx = voice_service.conversation.get_context()
        assert any("what is your name" in turn.get("text", "") for turn in ctx)
