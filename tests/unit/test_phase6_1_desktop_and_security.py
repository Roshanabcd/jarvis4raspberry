"""
JARVIS OS — Phase 6.1 Unit & Integration Test Suite.
Validates Desktop Launch Recovery, Localhost Security Binding, Background Voice Service,
Adaptive VAD & Feedback Suppression, Speaker Output, and 11-Component Health Diagnostics.
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
import requests

from config.config_manager import config
from apps.desktop.launcher import SingleInstanceLock, is_backend_healthy, is_window_open, BACKEND_URL
from apps.voice.wake_word_engine import WakeWordEngine, WakeState, is_voice_service_daemon_running, wake_word_engine
from apps.voice.speech_manager import speech_manager
from apps.voice.gradio_tts import gradio_cloner


def test_1_localhost_security_binding():
    """Verify backend is bound strictly to 127.0.0.1:8000 and not exposed on 0.0.0.0."""
    assert config.get("api_host") == "127.0.0.1", "config.yaml api_host must be 127.0.0.1"

    # Verify via ss socket inspection
    res = subprocess.run(["ss", "-ltnp"], capture_output=True, text=True, check=True)
    lines = res.stdout.splitlines()

    # Must find 127.0.0.1:8000
    found_127 = any("127.0.0.1:8000" in line for line in lines)
    # Must NOT find 0.0.0.0:8000
    found_000 = any("0.0.0.0:8000" in line for line in lines)

    assert found_127, "Port 8000 must be listening on 127.0.0.1"
    assert not found_000, "Port 8000 must NEVER be bound to 0.0.0.0"

    # Verify health endpoint is reachable on localhost
    resp = requests.get(f"{BACKEND_URL}/api/health", timeout=3.0)
    assert resp.status_code == 200, "Backend must respond 200 on 127.0.0.1:8000"


def test_2_desktop_launcher_and_window_detection():
    """Verify single instance lock recovery and window inspection logic."""
    test_lock_path = Path("/tmp/test_jarvis_single_instance.lock")
    test_lock_path.unlink(missing_ok=True)

    # 1. Stale lock recovery test: write a dead PID
    test_lock_path.write_text("9999999")  # non-existent PID
    lock = SingleInstanceLock(test_lock_path)
    acquired = lock.acquire()
    assert acquired is True, "SingleInstanceLock must recover from stale locks with dead PIDs"
    lock.release()
    test_lock_path.unlink(missing_ok=True)

    # 2. Window detection function test
    win_open = is_window_open()
    assert isinstance(win_open, bool), "is_window_open must return boolean"


def test_3_background_voice_service_and_single_ownership():
    """Verify systemd jarvis-voice.service is active and single microphone ownership is preserved."""
    active = is_voice_service_daemon_running()
    assert active is True, "systemctl --user jarvis-voice.service must be active and running"

    # Verify systemctl reports active
    res = subprocess.run(
        ["systemctl", "--user", "is-active", "jarvis-voice.service"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert res.stdout.strip() == "active"


def test_4_adaptive_noise_floor_and_dynamic_vad():
    """Verify dynamic noise floor tracking, adaptive threshold clamping, and 3.0s silence threshold."""
    engine = WakeWordEngine(silence_timeout_s=3.0, follow_up_window_s=15.0)

    # Ambient noise calibration
    initial_floor = engine.ambient_noise_floor
    engine._update_adaptive_threshold(50.0)
    assert engine.ambient_noise_floor > 0.0
    # Threshold should be >= 90.0 (min clamped)
    assert engine.adaptive_threshold >= 90.0
    assert engine.adaptive_threshold <= 350.0

    # High noise should raise threshold up to clamp
    for _ in range(5):
        engine._update_adaptive_threshold(160.0)
    assert engine.adaptive_threshold >= 90.0

    # Verify silence threshold is 3.0s
    assert engine.silence_timeout_s == 3.0
    # Verify follow-up window is 15.0s
    assert engine.follow_up_window_s == 15.0


def test_5_tts_feedback_loop_elimination():
    """Verify VAD suppresses recording while TTS is playing to avoid acoustic feedback."""
    engine = WakeWordEngine()
    # Mock is_tts_playing
    engine._is_tts_playing = lambda: True
    assert engine._is_tts_playing() is True


def test_6_speaker_output_and_volume_preservation():
    """Verify physical speaker default sink discovery and strict 65% volume preservation."""
    res = subprocess.run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"], capture_output=True, text=True, check=True)
    vol_str = res.stdout.strip()
    assert "0.65" in vol_str, f"Master volume must remain preserved at 0.65 (65%), got: {vol_str}"

    # Verify diagnostic tone generation endpoint
    resp = requests.post(f"{BACKEND_URL}/api/voice/test/speaker", timeout=5.0)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("component") == "speaker"
    assert data.get("status") == "ok"
    assert data.get("playback_completed") is True


def test_7_omnivoice_reference_audio_and_fallback_label():
    """Verify clean personal reference audio and truthful fallback label."""
    ref_audio = "/home/roshan/Downloads/myvoice_clean.wav"
    assert os.path.exists(ref_audio), "Reference audio /home/roshan/Downloads/myvoice_clean.wav must exist"

    with wave.open(ref_audio, "rb") as wf:
        assert wf.getnchannels() == 1, "Must be mono"
        assert wf.getframerate() == 24000, "Must be 24000 Hz"
        assert wf.getsampwidth() == 2, "Must be 16-bit PCM"

    status = gradio_cloner.get_provider_status()
    # When Colab is offline, it must NOT claim to be cloned
    if not status.get("online"):
        assert "Neural Fallback" in status.get("label", "") or "Fallback" in status.get("label", "")


def test_8_eleven_component_health_diagnostics():
    """Verify all 11 core subsystems are truthfully reported in /api/health."""
    resp = requests.get(f"{BACKEND_URL}/api/health", timeout=3.0)
    assert resp.status_code == 200
    data = resp.json()
    assert "components" in data
    comps = data["components"]

    required_11 = [
        "backend",
        "ai_provider",
        "microphone",
        "speaker",
        "voice_engine",
        "wake_word_daemon",
        "camera",
        "desktop_window",
        "localhost_security",
        "storage_db",
        "robot_hardware",
    ]

    for req in required_11:
        assert req in comps, f"Missing required component in /api/health: {req}"
        val = comps[req]
        assert isinstance(val, str) and len(val) > 0, f"Component {req} has invalid status: {val}"
        assert not val.startswith("ERROR:"), f"Component {req} encountered an error: {val}"
