"""
Tests for Gradio Voice Cloning TTS Integration and Fallback Mechanism.
"""

import os
import wave
import pytest
from apps.voice.gradio_tts import GradioVoiceCloner, AudioResult


class TestGradioVoiceCloner:
    @pytest.fixture
    def cloner(self, tmp_path):
        cache_dir = str(tmp_path / "voice_cache")
        return GradioVoiceCloner(
            gradio_url="https://13f7044a4e78090fd2.gradio.live/",
            cache_dir=cache_dir
        )

    def test_provider_status_offline_handling(self, cloner):
        """Verify provider status handles expired / unreachable Gradio link gracefully."""
        status = cloner.get_provider_status()
        assert status["name"] == "gradio_voice_clone"
        assert status["online"] is False
        assert "fallback_backend" in status
        assert status["cache_entries"] == 0

    def test_synthesize_empty_string(self, cloner):
        """Empty input should safely return an error AudioResult."""
        res = cloner.synthesize("")
        assert res.success is False
        assert res.error == "Empty text"

    def test_synthesize_offline_fallback(self, cloner):
        """When Gradio link is unreachable, cloner must fall back to local TTS."""
        res = cloner.synthesize("Unit test speech synthesis")
        assert res.success is True
        assert res.provider == "fallback_local_tts"
        assert res.cached is False

    def test_audio_file_validation(self, cloner, tmp_path):
        """Verify header validation for WAV files."""
        # Valid WAV
        valid_wav = tmp_path / "valid.wav"
        with wave.open(str(valid_wav), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b"\x00\x00" * 1600)
        assert cloner._validate_audio_file(str(valid_wav)) is True

        # Corrupt / empty file
        empty_file = tmp_path / "empty.wav"
        empty_file.write_bytes(b"")
        assert cloner._validate_audio_file(str(empty_file)) is False

        # Truncated header
        truncated = tmp_path / "truncated.wav"
        truncated.write_bytes(b"RIFFjunk")
        assert cloner._validate_audio_file(str(truncated)) is False

    def test_caching_behavior(self, cloner, tmp_path):
        """Pre-populate a valid cached audio file and verify cache hit."""
        text = "System diagnostics complete"
        cache_path = cloner._get_cache_path(text)

        with wave.open(cache_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b"\x00\x00" * 1600)

        res = cloner.synthesize(text)
        assert res.success is True
        assert res.cached is True
        assert res.provider == "cache"
        assert res.audio_path == cache_path

    def test_stop_playback_when_no_active_player(self, cloner):
        """Calling stop_playback when nothing is playing should be a clean no-op."""
        cloner.stop_playback()
        assert cloner._current_player is None

    def test_validate_mp3_and_reference_audio(self, tmp_path):
        """Verify audio validator accepts MPEG/MP3 audio and rejects non-audio."""
        cache_dir = str(tmp_path / "voice_cache")
        cloner = GradioVoiceCloner(gradio_url="http://disabled", cache_dir=cache_dir)
        
        # Valid MP3 sync frame header (MPEG-1 Layer 3)
        valid_mp3 = tmp_path / "sample.mp3"
        valid_mp3.write_bytes(b"\xff\xfb\x90\x44" + b"\x00" * 300)
        assert cloner._validate_audio_file(str(valid_mp3)) is True

        # Valid ID3v2 tag
        valid_id3 = tmp_path / "sample_id3.mp3"
        valid_id3.write_bytes(b"ID3\x03\x00\x00\x00\x00\x00\x10" + b"\x00" * 300)
        assert cloner._validate_audio_file(str(valid_id3)) is True

        # HTML 404 or text file pretending to be audio (>100 bytes)
        fake_audio = tmp_path / "fake.wav"
        fake_audio.write_bytes(b"<html><head><title>404 Not Found</title></head><body><h1>404 Not Found</h1><p>The requested URL was not found on this server.</p></body></html>" + b" " * 100)
        assert cloner._validate_audio_file(str(fake_audio)) is False
