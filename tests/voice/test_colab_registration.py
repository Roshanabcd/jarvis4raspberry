"""
Tests for Google Colab OmniVoice Dynamic Registration and Provider Handover.
"""

import os
import tempfile
import pytest

from apps.voice.colab_registration import ColabRegistrationManager
from apps.voice.gradio_tts import GradioVoiceCloner, AudioResult


class TestColabRegistration:
    @pytest.fixture
    def temp_manager(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name
        mgr = ColabRegistrationManager(state_file=temp_path, monitor_enabled=False)
        mgr.registration_token = "test-registration-token"
        yield mgr
        mgr.stop_background_monitor()
        if os.path.exists(temp_path):
            os.remove(temp_path)

    def test_url_validation_valid(self, temp_manager):
        valid, msg = temp_manager.validate_url("https://abc12345.gradio.live")
        assert valid is True
        assert msg == ""

        valid, msg = temp_manager.validate_url("https://my-space.hf.space")
        assert valid is True

    def test_url_validation_rejects_non_https_and_invalid(self, temp_manager):
        valid, msg = temp_manager.validate_url("ftp://example.com")
        assert valid is False
        assert "Invalid URL scheme" in msg

        valid, msg = temp_manager.validate_url("")
        assert valid is False

    def test_url_validation_rejects_ssrf_loopback(self, temp_manager):
        valid, msg = temp_manager.validate_url("https://localhost:8000")
        assert valid is False
        assert "loopback" in msg.lower() or "private" in msg.lower()

        valid, msg = temp_manager.validate_url("https://127.0.0.1:8000")
        assert valid is False

        valid, msg = temp_manager.validate_url("https://192.168.1.100:8000")
        assert valid is False

    def test_token_authentication(self, temp_manager):
        # Invalid token rejected
        res = temp_manager.register_url(
            gradio_url="https://test.gradio.live",
            token="wrong_token",
            is_local_request=False,
            verify_now=False,
        )
        assert res["status"] == "error"
        assert res["code"] == 401

        # Valid token accepted
        res = temp_manager.register_url(
            gradio_url="https://test.gradio.live",
            token="test-registration-token",
            is_local_request=False,
            verify_now=False,
        )
        assert res["status"] == "ok"
        assert res["runtime_status"] == "ready"
        assert temp_manager.get_active_url() == "https://test.gradio.live"

    def test_state_persistence(self, temp_manager):
        temp_manager.register_url(
            gradio_url="https://persisted-test.gradio.live",
            token="test-registration-token",
            session_id="sess_123",
            is_local_request=True,
            verify_now=False,
        )
        # Re-instantiate from the same state file
        new_mgr = ColabRegistrationManager(state_file=temp_manager.state_file)
        assert new_mgr.get_active_url() == "https://persisted-test.gradio.live"
        assert new_mgr.state.get("session_id") == "sess_123"

    def test_mark_offline(self, temp_manager):
        temp_manager.register_url(
            gradio_url="https://online.gradio.live",
            is_local_request=True,
            verify_now=False,
        )
        assert temp_manager.state["runtime_status"] == "ready"
        temp_manager.mark_offline("Connection dropped")
        assert temp_manager.state["runtime_status"] == "offline"
        assert temp_manager.state["last_error"] == "Connection dropped"

    def test_monitor_does_not_start_without_explicit_opt_in(self, temp_manager):
        assert temp_manager.get_status()["monitor_enabled"] is False
        assert temp_manager.get_status()["monitor_running"] is False
        temp_manager.register_url(
            gradio_url="https://manual-test.gradio.live",
            is_local_request=True,
            verify_now=False,
        )
        assert temp_manager.get_status()["monitor_running"] is False


class TestGradioVoiceClonerIntegration:
    def test_update_url_resets_client(self):
        cloner = GradioVoiceCloner(gradio_url="https://old.gradio.live")
        cloner.update_url("https://new.gradio.live")
        assert cloner.gradio_url == "https://new.gradio.live"
        assert cloner._client is None
        assert cloner._online is None

    def test_reference_audio_discovery(self):
        cloner = GradioVoiceCloner()
        # Should have found a valid reference sample if myvoice exists
        if os.path.exists("/home/roshan/Downloads/myvoice.mp3") or os.path.exists("/home/roshan/Downloads/myvoice_clean.wav"):
            assert cloner.reference_voice_path is not None
            assert "myvoice" in cloner.reference_voice_path
            assert os.path.exists(cloner.reference_voice_path)
        elif os.path.exists("/home/roshan/.gemini/antigravity/scratch/jarvis-os/data/voice_samples/myvoice.wav"):
            assert cloner.reference_voice_path is not None
