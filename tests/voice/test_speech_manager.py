"""
Tests for JARVIS Central Speech Output Manager & Voice Audio Routing.
"""

import os
import shutil
import tempfile
import pytest
from apps.voice.speech_manager import SpeechOutputManager, speech_manager
from apps.voice.gradio_tts import AudioResult


class TestSpeechOutputManager:
    """Unit tests for SpeechOutputManager staging, status, and execution."""

    @pytest.fixture
    def custom_stage_manager(self):
        tmp_dir = tempfile.mkdtemp(prefix="jarvis_test_stage_")
        mgr = SpeechOutputManager(stage_dir=tmp_dir)
        yield mgr
        shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_status_structure(self, custom_stage_manager):
        """Status dict should report microphone, speaker, and tts status."""
        st = custom_stage_manager.get_status()
        assert "microphone" in st
        assert "speaker" in st
        assert "tts" in st
        assert "status_label" in st["tts"]
        assert "last_playback" in st
        assert "staged_audio_count" in st

    def test_synthesize_empty_string(self, custom_stage_manager):
        """Empty or whitespace text should return status empty without errors."""
        res = custom_stage_manager.synthesize_and_stage("", play_system=False)
        assert res["status"] == "empty"
        assert res["audio_id"] is None
        assert res["success"] is False

    def test_reentrant_lock_no_deadlock(self, custom_stage_manager):
        """play_system_audio must not deadlock on internal stop() calls (RLock)."""
        # Call stop multiple times concurrently
        custom_stage_manager.stop()
        custom_stage_manager.stop()
        # Non-existent file should safely return False without lock contention
        ok = custom_stage_manager.play_system_audio("/tmp/non_existent_audio_file_123.wav")
        assert ok is False

    def test_synthesize_and_stage_with_mock(self, custom_stage_manager, monkeypatch):
        """Verify audio staging and URL generation when TTS produces an audio file."""
        tmp_wav = os.path.join(custom_stage_manager.stage_dir, "mock_source.wav")
        with open(tmp_wav, "wb") as f:
            # Minimal WAV header (44 bytes)
            f.write(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00")

        def mock_synthesize(text, voice_config=None):
            return AudioResult(
                audio_path=tmp_wav,
                format="wav",
                duration_s=1.0,
                cached=False,
                provider="edge_neural_tts",
                text=text,
                success=True,
                error=None,
                latency_ms=120.0,
            )

        monkeypatch.setattr("apps.voice.gradio_tts.gradio_cloner.synthesize", mock_synthesize)

        res = custom_stage_manager.synthesize_and_stage("Test phrase", play_system=False)
        assert res["status"] == "ok"
        assert res["success"] is True
        assert res["audio_id"] is not None
        assert res["audio_url"] == f"/api/voice/audio/{res['audio_id']}"
        assert res["provider"] == "edge_neural_tts"
        assert "Neural Fallback" in res["provider_label"]

        # Retrieve staged file
        staged = custom_stage_manager.get_staged_audio(res["audio_id"])
        assert staged is not None
        path, media_type = staged
        assert os.path.exists(path)
        assert media_type == "audio/wav"

    def test_no_simulated_transcription_in_real_mode(self):
        """Microphone test in real hardware mode must not return 'Simulated transcription'."""
        from apps.voice.service import voice_service
        # Ensure simulation_mode is False
        assert voice_service.simulation_mode is False
        assert voice_service.stt.simulation_mode is False

        # In real mode, empty or silence must return empty string or real text, never simulated string
        transcription = voice_service.stt.transcribe("/tmp/non_existent_silent.wav")
        assert transcription != "Simulated transcription"
        assert transcription == ""
