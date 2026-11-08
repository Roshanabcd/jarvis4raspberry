"""Phase 4 Test Suite — Custom Cloned Voice, OmniVoice/Gradio, and Neural Fallback."""
import os
import time
import pytest
from fastapi.testclient import TestClient

from apps.core.main import app
from apps.voice.gradio_tts import GradioVoiceCloner, sanitize_speech_text, gradio_cloner


class TestPhase4VoiceCloning:
    """Test suite verifying Phase 4 custom voice cloning and caching pipeline."""

    def test_speech_sanitization(self):
        raw = "Hello **Tony**, this is `code`! [sigh] # Status Report"
        clean = sanitize_speech_text(raw)
        assert "**" not in clean
        assert "`" not in clean
        assert "[sigh]" not in clean
        assert "#" not in clean
        assert "Hello Tony, this is code! Status Report" == clean

    def test_reference_audio_binding(self):
        cloner = GradioVoiceCloner()
        status = cloner.get_provider_status()
        assert status["has_reference_audio"] is True
        assert "myvoice.wav" in status["reference_audio_path"]
        assert os.path.exists(status["reference_audio_path"])

    def test_sha256_cache_hit_under_5ms(self):
        phrase = "Phase 4 Caching Performance Verification"
        # First call caches
        res1 = gradio_cloner.synthesize(phrase)
        assert res1.success is True

        # Second call must hit cache in <5ms
        t0 = time.perf_counter()
        res2 = gradio_cloner.synthesize(phrase)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        assert res2.success is True
        assert res2.cached is True
        assert res2.provider == "cache"
        assert res2.audio_path is not None
        assert elapsed_ms < 5.0, f"Cache retrieval took {elapsed_ms:.2f}ms, expected <5ms"

    def test_preflight_probe_does_not_hang(self):
        # A dead or unreachable URL should probe in <3s and cleanly mark offline
        t0 = time.time()
        cloner = GradioVoiceCloner(gradio_url="https://127.0.0.1:59999/unreachable")
        is_online = cloner._probe_gradio_client(force=True)
        elapsed = time.time() - t0

        assert is_online is False
        assert elapsed < 4.0

    def test_audio_file_validator(self, tmp_path):
        cloner = GradioVoiceCloner()
        empty_file = str(tmp_path / "empty.wav")
        with open(empty_file, "wb") as f:
            f.write(b"")
        assert cloner._validate_audio_file(empty_file) is False

        # Valid mock wav header
        wav_file = str(tmp_path / "valid.wav")
        with open(wav_file, "wb") as f:
            f.write(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00")
        assert cloner._validate_audio_file(wav_file) is True

    def test_api_synthesize_endpoint(self):
        client = TestClient(app)
        res = client.post("/api/voice/synthesize", json={"text": "System diagnostics nominal."})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["provider"] in ("cache", "edge_neural_tts", "espeak_local_tts", "gradio_voice_clone", "fallback_local_tts")
