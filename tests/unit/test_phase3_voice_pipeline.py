"""Phase 3 Test Suite — Audio Input, STT, Wake-Word, and Voice Pipeline Tests."""
import os
import pytest
from fastapi.testclient import TestClient

from apps.core.main import app
from apps.voice.audio_manager import AudioManager
from apps.voice.wake_word import WakeWordDetector
from apps.voice.stt import SpeechToText
from apps.voice.service import VoiceService, voice_service


class TestPhase3VoicePipeline:
    """Test suite verifying Phase 3 Voice subsystem and API."""

    def test_audio_manager_devices_and_identifiers(self):
        mgr = AudioManager(simulation_mode=True)
        dev = {"card": 2, "device": 0, "name": "ReSpeaker Lite"}
        assert mgr.get_device_alsa_identifier(dev, plug=False) == "hw:2,0"
        assert mgr.get_device_alsa_identifier(dev, plug=True) == "plughw:2,0"
        assert mgr.get_record_alsa_identifier(dev) == "plughw:2,0"

        # Check playback detection
        pdevs = mgr.detect_playback_devices()
        assert len(pdevs) >= 1
        best_p = mgr.select_best_playback_device()
        assert best_p is not None

    def test_wake_word_detection_variations(self):
        detector = WakeWordDetector(wake_word="jarvis")
        assert detector.detect("Hello JARVIS, what is the status?") is True
        assert detector.detect("Hey jarvis report diagnostics") is True
        assert detector.detect("jar vis activate robot") is True
        assert detector.detect("Good morning javis") is True
        assert detector.detect("Hey Alexa order pizza") is False
        assert detector.detect("") is False

    def test_stt_recording_and_transcribe(self, tmp_path):
        stt = SpeechToText(simulation_mode=True)
        rec_path = str(tmp_path / "test_voice.wav")
        success = stt.record_audio(duration_secs=1, output_path=rec_path)
        assert success is True
        assert os.path.exists(rec_path)
        assert os.path.getsize(rec_path) > 0

        # Transcribe simulation
        text = stt.transcribe(rec_path)
        assert text == "Simulated transcription"

    def test_voice_service_state_and_mute(self):
        service = VoiceService(simulation_mode=True)
        state = service.get_state()
        assert state["state"] in ("STANDBY", "LISTENING", "MUTED")
        assert "device" in state
        assert "wake_word" in state

        # Test mute/unmute
        service.mute()
        assert service.is_muted() is True
        assert service.get_state()["muted"] is True

        service.unmute()
        assert service.is_muted() is False
        assert service.get_state()["muted"] is False

    def test_voice_api_status_and_devices(self):
        client = TestClient(app)
        res = client.get("/api/voice/status")
        assert res.status_code == 200
        data = res.json()
        assert "state" in data
        assert "listening" in data
        assert "device" in data
        assert "wake_word" in data

        res_dev = client.get("/api/voice/devices")
        assert res_dev.status_code == 200
        dev_data = res_dev.json()
        assert "input_devices" in dev_data
        assert "output_devices" in dev_data
        assert "selected_input" in dev_data
        assert "selected_output" in dev_data

    def test_voice_api_command(self):
        client = TestClient(app)
        res = client.post("/api/voice/command", json={"text": "what is your name"})
        assert res.status_code == 200
        assert "response" in res.json()
        assert len(res.json()["response"]) > 0
