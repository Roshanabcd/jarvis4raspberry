"""Unit and Integration Tests for JARVIS OS Voice Subsystem.

Tests AudioManager, WakeWordDetector, SpeechToText, TextToSpeech,
ConversationManager, and VoiceService end-to-end pipeline.
"""

import asyncio
import os
import shutil
import tempfile
import time
import pytest

from apps.voice.audio_manager import AudioManager
from apps.voice.wake_word import WakeWordDetector
from apps.voice.stt import SpeechToText
from apps.voice.tts import TextToSpeech
from apps.voice.conversation import ConversationManager
from apps.voice.service import VoiceService


# ─────────────────────────────────────────────────────────────
# 1. AudioManager Tests
# ─────────────────────────────────────────────────────────────
class TestAudioManager:
    def test_simulation_detect_devices(self):
        mgr = AudioManager(simulation_mode=True)
        devices = mgr.detect_devices()
        assert len(devices) == 1
        assert devices[0]["name"] == "Simulated"
        assert devices[0]["card"] == 0
        assert devices[0]["device"] == 0

    def test_simulation_select_best_device(self):
        mgr = AudioManager(simulation_mode=True)
        best = mgr.select_best_device()
        assert best["name"] == "Simulated"
        assert best["card"] == 0

    def test_device_selection_respeaker_preference(self, monkeypatch):
        mgr = AudioManager(simulation_mode=False)
        fake_devices = [
            {"card": 0, "device": 0, "name": "bcm2835 Headphones"},
            {"card": 1, "device": 0, "name": "Seeed ReSpeaker Lite Audio"},
            {"card": 2, "device": 0, "name": "USB PnP Sound Device"},
        ]
        monkeypatch.setattr(mgr, "detect_devices", lambda: fake_devices)
        selected = mgr.select_best_device()
        assert selected["card"] == 1
        assert "ReSpeaker" in selected["name"]

    def test_device_selection_fallback_first(self, monkeypatch):
        mgr = AudioManager(simulation_mode=False)
        fake_devices = [
            {"card": 0, "device": 0, "name": "Generic USB Mic"},
            {"card": 2, "device": 0, "name": "Headset"},
        ]
        monkeypatch.setattr(mgr, "detect_devices", lambda: fake_devices)
        selected = mgr.select_best_device()
        assert selected["card"] == 0
        assert selected["name"] == "Generic USB Mic"

    def test_alsa_identifier(self):
        mgr = AudioManager(simulation_mode=True)
        dev = {"card": 1, "device": 0, "name": "ReSpeaker"}
        assert mgr.get_device_alsa_identifier(dev) == "hw:1,0"
        sim_dev = {"card": 0, "device": 0, "name": "Simulated"}
        assert mgr.get_device_alsa_identifier(sim_dev) == "default"


# ─────────────────────────────────────────────────────────────
# 2. WakeWordDetector Tests
# ─────────────────────────────────────────────────────────────
class TestWakeWordDetector:
    def test_default_detection(self):
        detector = WakeWordDetector(wake_word="jarvis")
        assert detector.detect("Hey Jarvis please help") is True
        assert detector.detect("JARVIS what is the time") is True
        assert detector.detect("Can you hear me jarvis?") is True
        assert detector.detect("Hey Siri what is the time") is False

    def test_custom_wake_word(self):
        detector = WakeWordDetector(wake_word="computer")
        assert detector.detect("Computer, initiate diagnostics") is True
        assert detector.detect("Jarvis, report status") is False

    def test_empty_and_invalid_inputs(self):
        detector = WakeWordDetector(wake_word="jarvis")
        assert detector.detect("") is False
        assert detector.detect("   ") is False


# ─────────────────────────────────────────────────────────────
# 3. SpeechToText (STT) Tests
# ─────────────────────────────────────────────────────────────
class TestSpeechToText:
    def test_transcribe_simulated(self):
        stt = SpeechToText(simulation_mode=True)
        result = stt.transcribe_simulated()
        assert result == "Simulated transcription"

    def test_transcribe_in_simulation_mode(self):
        stt = SpeechToText(simulation_mode=True)
        text = stt.transcribe("/tmp/nonexistent.wav")
        assert text == "Simulated transcription"

    def test_record_audio_creates_dummy_wav(self, tmp_path):
        stt = SpeechToText(simulation_mode=True)
        out_file = str(tmp_path / "test_recording.wav")
        success = stt.record_audio(duration_secs=1, output_path=out_file)
        assert success is True
        assert os.path.exists(out_file)
        assert os.path.getsize(out_file) > 0


# ─────────────────────────────────────────────────────────────
# 4. TextToSpeech (TTS) Tests
# ─────────────────────────────────────────────────────────────
class TestTextToSpeech:
    def test_speak_async(self):
        tts = TextToSpeech(simulation_mode=True)
        # Should not raise exception
        tts.speak_sync("System initialized successfully.")

    def test_speak_sync(self):
        tts = TextToSpeech(simulation_mode=True)
        # Synchronous execution
        tts.speak_sync("Synchronous voice test passed.")

    def test_configurable_attributes(self):
        tts = TextToSpeech(rate=180, volume=0.8, language="en", simulation_mode=True)
        assert tts.rate == 180
        assert tts.volume == 0.8
        assert tts.language == "en"
        assert tts.simulation_mode is True


# ─────────────────────────────────────────────────────────────
# 5. ConversationManager Tests
# ─────────────────────────────────────────────────────────────
class TestConversationManager:
    @pytest.fixture
    def conv_manager(self, tmp_path):
        return ConversationManager(timeout_seconds=5, storage_dir=str(tmp_path))

    def test_start_and_add_turns(self, conv_manager):
        session_id = conv_manager.start_session("test_sess_01")
        assert session_id == "test_sess_01"
        assert conv_manager.is_session_active() is True

        conv_manager.add_turn("user", "Hello Jarvis")
        conv_manager.add_turn("assistant", "Greetings, how can I assist?")

        context = conv_manager.get_context(limit=10)
        assert len(context) == 2
        assert context[0]["role"] == "user"
        assert context[0]["text"] == "Hello Jarvis"
        assert context[1]["role"] == "assistant"
        assert context[1]["text"] == "Greetings, how can I assist?"

    def test_end_session_persists_json(self, conv_manager, tmp_path):
        conv_manager.start_session("sess_persist")
        conv_manager.add_turn("user", "Testing persistence")
        conv_manager.end_session()

        assert conv_manager.is_session_active() is False
        expected_file = tmp_path / "sess_persist.json"
        assert expected_file.exists()

    def test_session_timeout(self, conv_manager):
        conv_manager.timeout_seconds = 1  # 1 second timeout
        conv_manager.start_session("short_sess")
        conv_manager.add_turn("user", "first message")
        time.sleep(1.2)
        assert conv_manager.is_session_active() is False


# ─────────────────────────────────────────────────────────────
# 6. VoiceService Integration Tests
# ─────────────────────────────────────────────────────────────
class TestVoiceService:
    def test_service_initialization(self):
        service = VoiceService(wake_word="jarvis", simulation_mode=True)
        assert service.wake_detector.wake_word == "jarvis"
        assert service.simulation_mode is True
        assert service.listening is False

    def test_process_command_returns_response(self):
        service = VoiceService(simulation_mode=True)
        reply = service.process_command("what is the system status")
        assert isinstance(reply, str)
        assert len(reply) > 0

    def test_service_start_stop(self):
        service = VoiceService(simulation_mode=True)
        service.start()
        assert service.listening is True
        assert service._thread is not None
        assert service._thread.is_alive()

        # Clean stop
        service.stop()
        assert service.listening is False
        assert service._thread is None
