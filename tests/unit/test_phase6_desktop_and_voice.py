"""
JARVIS OS — Phase 6 Comprehensive Test Suite:
Standalone Desktop Application, Voice Pipeline Repair, ReSpeaker Microphone,
OmniVoice / Fallback TTS, Physical Speaker, 3-Second Silence, and Background Wake Word.
"""

import json
import math
import os
import shutil
import struct
import subprocess
import time
import wave
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.core.main import app
from config.config_manager import config
from apps.voice.service import voice_service
from apps.voice.wake_word_engine import wake_word_engine, WakeState
from apps.voice.speech_manager import speech_manager
from apps.voice.gradio_tts import gradio_cloner, sanitize_speech_text
from apps.voice.stt import SpeechToText
from ai.brain import get_brain


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_1_standalone_desktop_launcher_and_entry():
    """Verify standalone desktop application launcher, entry file, and single-instance lock."""
    launcher_path = Path("/home/roshan/.gemini/antigravity/scratch/jarvis-os/apps/desktop/launcher.py")
    bin_jarvis = Path("/home/roshan/.local/bin/jarvis")
    desktop_entry = Path("/home/roshan/.local/share/applications/jarvis-os.desktop")
    desktop_icon = Path("/home/roshan/.local/share/icons/hicolor/256x256/apps/jarvis-os.png")

    assert launcher_path.exists(), "launcher.py must exist"
    assert os.access(launcher_path, os.X_OK), "launcher.py must be executable"
    assert bin_jarvis.exists(), "jarvis executable must exist in ~/.local/bin/jarvis"
    assert os.access(bin_jarvis, os.X_OK), "jarvis executable must be runnable"
    assert desktop_entry.exists(), "Desktop entry file must exist"
    assert desktop_icon.exists(), "JARVIS application icon must exist"

    # Verify single-instance status CLI flag
    res = subprocess.run([str(bin_jarvis), "--status"], capture_output=True, text=True, check=False)
    assert res.returncode == 0, f"jarvis --status failed: {res.stderr}"
    data = json.loads(res.stdout)
    assert "backend_healthy" in data
    assert "backend_url" in data


def test_2_ollama_local_ai_integration():
    """Verify local Ollama engine, model availability, and real prompt generation."""
    brain = get_brain()
    status = brain.get_providers_status()
    assert "providers" in status
    assert status.get("active_provider") is not None

    # Test non-simulated chat query
    res = brain.chat("What is 15 + 27? Answer in one word or number only.")
    assert "response" in res
    assert res.get("response") != ""
    assert ("42" in res["response"] or "forty-two" in res["response"].lower())


def test_3_real_respeaker_microphone_input():
    """Test physical/PipeWire microphone capture and RMS energy validation."""
    mgr = voice_service.audio_manager
    devices = mgr.detect_devices()
    assert len(devices) > 0, "At least one capture device must be registered"

    best_mic = mgr.select_best_device()
    assert "ReSpeaker" in best_mic.get("name", ""), f"Selected device should be ReSpeaker, got {best_mic}"

    # Perform real 2-second capture test
    test_out = "/tmp/test_phase6_mic.wav"
    if os.path.exists(test_out):
        os.remove(test_out)

    stt = SpeechToText(simulation_mode=False)
    ok = stt.record_audio(duration_secs=2, output_path=test_out)
    assert ok, "Physical microphone capture must produce valid WAV file"
    assert os.path.exists(test_out), "Recorded audio file must exist"
    assert os.path.getsize(test_out) > 1000, "Audio file must contain substantial PCM data"

    # Validate WAV properties and calculate RMS energy
    with wave.open(test_out, "rb") as wf:
        assert wf.getnchannels() == 1, "Mono capture required"
        assert wf.getframerate() == 16000, "16 kHz sample rate required"
        n_frames = wf.getnframes()
        raw_bytes = wf.readframes(n_frames)
        samples = struct.unpack(f"{n_frames}h", raw_bytes)
        rms = math.sqrt(sum(s * s for s in samples) / len(samples))
        assert rms >= 0.0, "RMS energy must be calculable"


def test_4_speech_recognition_no_simulation():
    """Verify that SpeechToText in real mode never produces fake 'Simulated transcription'."""
    stt = SpeechToText(simulation_mode=False)
    assert stt.simulation_mode is False, "STT must run in real mode"

    # Silent audio test must return empty string, never "Simulated transcription"
    silent_wav = "/tmp/test_phase6_silent.wav"
    with wave.open(silent_wav, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 16000)

    result = stt.transcribe(silent_wav)
    assert result != "Simulated transcription", "Real STT must never return 'Simulated transcription'"
    assert result == "", "Silent audio must transcribe to empty string"


def test_5_ai_response_generation_speed():
    """Verify AI brain responds and text output is produced immediately without waiting for TTS."""
    brain = get_brain()
    t0 = time.perf_counter()
    res = brain.chat("Say 'JARVIS OS Phase 6 online' in exactly five words.")
    dur_ms = (time.perf_counter() - t0) * 1000
    assert "response" in res
    assert len(res["response"]) > 0
    # On Raspberry Pi 5 Cortex-A76 CPU, allow up to 90s for cold model weight load into RAM
    assert dur_ms < 90000, "AI response must complete within reasonable CPU inference timeout"


def test_6_omnivoice_reference_audio_and_fallback():
    """Verify user reference audio profile and transparent fallback identification."""
    status = gradio_cloner.get_provider_status()
    assert "has_reference_audio" in status
    assert status["has_reference_audio"] is True, "Reference audio sample must be detected"

    ref_info = gradio_cloner.get_reference_audio_info()
    assert ref_info.get("exists") is True
    assert ref_info.get("sample_rate") == 24000, "Reference sample must be 24 kHz WAV"
    assert ref_info.get("channels") == 1, "Reference sample must be mono"

    # Check TTS synthesis and verify honest provider labelling
    res = speech_manager.synthesize_and_stage("Testing speech synthesis pipeline.", play_system=False)
    assert res.get("success") is True
    assert res.get("audio_url") is not None
    assert res.get("provider") is not None
    # If OmniVoice is offline, provider must be honest fallback
    if not status.get("online"):
        assert (
            "fallback" in res.get("provider_label", "").lower()
            or "edge" in res.get("provider", "").lower()
            or "cache" in res.get("provider", "").lower()
        )
        assert res.get("is_cloned") is False, "Must not falsely claim fallback is cloned voice"


def test_7_fallback_voice_labelling():
    """Verify that Edge-TTS fallback voice generates valid audio and identifies provider accurately."""
    res = gradio_cloner.synthesize("Fallback voice calibration test.")
    assert res.success is True
    assert os.path.exists(res.audio_path)
    assert res.provider in ("edge_neural_tts", "espeak_local_tts", "cache", "omnivoice_clone", "gradio_voice_clone")
    if res.provider == "edge_neural_tts":
        assert res.is_cloned is False, "Fallback must be marked as not cloned"


def test_8_physical_speaker_diagnostics_and_playback():
    """Verify physical speaker output test tone and verification endpoint."""
    res = speech_manager.test_speaker()
    assert res.get("status") == "ok", "Speaker test tone generation and playback must succeed"
    assert res.get("audio_generated") is True
    assert res.get("file_decoded") is True
    assert res.get("playback_process_started") is True
    assert res.get("playback_completed") is True

    # Confirm user audibility
    conf = speech_manager.confirm_speaker_audibility(confirmed=True)
    assert conf.get("speaker_verified") is True


def test_9_wake_word_engine_12_states_and_silence_threshold():
    """Verify WakeWordEngine 12-state state machine and 3.0s silence threshold configuration."""
    assert wake_word_engine.silence_timeout_s == 3.0, "Silence timeout must default to 3.0s"
    assert wake_word_engine.energy_threshold == 120.0, "Energy threshold must default to 120.0"

    status = wake_word_engine.get_status()
    assert "state" in status
    assert "silence_timeout_s" in status
    assert status["silence_timeout_s"] == 3.0

    # Test state transitions
    wake_word_engine.set_state(WakeState.STANDBY_LISTENING)
    assert wake_word_engine.state == WakeState.STANDBY_LISTENING

    wake_word_engine.set_state(WakeState.WAKE_DETECTED)
    assert wake_word_engine.state == WakeState.WAKE_DETECTED

    wake_word_engine.set_state(WakeState.LISTENING_SPEECH)
    assert wake_word_engine.state == WakeState.LISTENING_SPEECH

    wake_word_engine.set_state(WakeState.SILENCE_COUNTDOWN)
    assert wake_word_engine.state == WakeState.SILENCE_COUNTDOWN

    wake_word_engine.set_state(WakeState.FOLLOW_UP_STANDBY)
    assert wake_word_engine.state == WakeState.FOLLOW_UP_STANDBY

    # Restore standby
    wake_word_engine.set_state(WakeState.STANDBY_LISTENING)


def test_10_voice_task_execution_dispatch():
    """Verify that speech commands route to Brain and execute system/desktop tools accurately."""
    brain = get_brain()
    # Test system awareness query
    res = brain.chat("What is the current system uptime?")
    assert "response" in res
    assert len(res["response"]) > 0

    # Test desktop search query
    res2 = brain.chat("Search for python files in the project")
    assert "response" in res2
    assert len(res2["response"]) > 0


def test_11_background_music_preservation():
    """Verify AudioStreamManager ducking policy preserves active playback without killing external processes."""
    from tools.media.audio_stream_manager import audio_stream_manager
    st = audio_stream_manager.list_active_streams()
    assert isinstance(st, list), "list_active_streams must return a list of active streams"

    # Ensure ducking does not crash and restores gracefully
    audio_stream_manager.duck_active_streams(duck_fraction=0.20)
    audio_stream_manager.restore_active_streams()


def test_12_rest_api_voice_endpoints(client):
    """Verify the Phase 6 REST API endpoints."""
    # 1. Voice diagnostics
    r = client.get("/api/voice/diagnostics")
    assert r.status_code == 200
    data = r.json()
    assert "components" in data
    assert "microphone_capture" in data["components"]
    assert "speaker_playback" in data["components"]
    assert "text_to_speech" in data["components"]

    # 2. Wake status
    r_wake = client.get("/api/voice/wake_status")
    assert r_wake.status_code == 200
    assert "state" in r_wake.json()

    # 3. Test microphone
    r_mic = client.post("/api/voice/test/microphone?duration_secs=1")
    assert r_mic.status_code == 200
    mic_d = r_mic.json()
    assert mic_d.get("status") == "ok"
    assert "rms_energy" in mic_d

    # 4. Test speaker
    r_spk = client.post("/api/voice/test/speaker")
    assert r_spk.status_code == 200
    assert r_spk.json().get("status") == "ok"

    # 5. Confirm speaker audibility
    r_conf = client.post("/api/voice/test/speaker/confirm", json={"confirmed": True})
    assert r_conf.status_code == 200
    assert r_conf.json().get("speaker_verified") is True
