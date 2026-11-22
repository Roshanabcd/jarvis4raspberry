import os
import subprocess
import tempfile
import wave
import pytest

from apps.voice.wake_word_engine import WakeWordEngine, WakeState, WAKE_PHRASES


def test_wake_phrases_include_both_hey_and_hello():
    engine = WakeWordEngine()
    assert engine._matches_wake_phrase("hello jarvis")
    assert engine._matches_wake_phrase("Hey Jarvis")
    assert engine._matches_wake_phrase("Wake up JARVIS, what time is it?")
    assert engine._matches_wake_phrase("ok jarvis")
    assert not engine._matches_wake_phrase("random room noise")
    assert not engine._matches_wake_phrase("the weather today is nice")


def test_command_after_wake_phrase_extraction():
    engine = WakeWordEngine()
    cmd1 = engine._command_after_wake_phrase("Hey Jarvis, what is the CPU temperature?")
    assert cmd1.lower() == "what is the cpu temperature?"

    cmd2 = engine._command_after_wake_phrase("Hello Jarvis turn on system lights")
    assert cmd2.lower() == "turn on system lights"


def test_acoustic_wake_detection_hey_jarvis():
    engine = WakeWordEngine()
    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = os.path.join(tmpdir, "hey.wav")
        subprocess.run(
            ["espeak-ng", "-s", "130", "-w", wav_path, "hey jarvis"],
            check=True,
            capture_output=True,
        )
        converted_path = os.path.join(tmpdir, "16k_hey.wav")
        subprocess.run(
            ["ffmpeg", "-y", "-i", wav_path, "-ar", "16000", "-ac", "1", converted_path],
            check=True,
            capture_output=True,
        )
        score = engine._score_acoustic_wake(converted_path)
        assert score >= 0.85, f"Expected acoustic score >= 0.85 for 'hey jarvis', got {score}"


def test_stt_wake_detection_dual_support():
    engine = WakeWordEngine()
    # Both "Hello Jarvis" and "Hey Jarvis" are supported wake phrases in speech recognition
    for phrase in ["Hello Jarvis", "Hey Jarvis", "wake up jarvis", "JARVIS"]:
        assert engine._matches_wake_phrase(phrase), f"Expected '{phrase}' to match wake phrases"


def test_boundary_frame_retention_and_stitching():
    engine = WakeWordEngine()
    with tempfile.TemporaryDirectory() as tmpdir:
        full_wav = os.path.join(tmpdir, "full.wav")
        subprocess.run(
            ["espeak-ng", "-s", "130", "-w", full_wav, "hey jarvis"],
            check=True,
            capture_output=True,
        )
        converted_wav = os.path.join(tmpdir, "converted.wav")
        subprocess.run(
            ["ffmpeg", "-y", "-i", full_wav, "-ar", "16000", "-ac", "1", converted_wav],
            check=True,
            capture_output=True,
        )

        with wave.open(converted_wav, "rb") as wf:
            params = wf.getparams()
            all_frames = wf.readframes(wf.getnframes())

        # Split frames into chunk1 ("hey") and chunk2 ("jarvis")
        # Split at 35% of audio so chunk1 has only "hey"
        split_idx = int(len(all_frames) * 0.35)
        # Ensure frame boundary (2 bytes per sample)
        split_idx -= split_idx % 2
        chunk1_frames = all_frames[:split_idx]
        chunk2_frames = all_frames[split_idx:]

        chunk1_wav = os.path.join(tmpdir, "chunk1.wav")
        with wave.open(chunk1_wav, "wb") as wf:
            wf.setparams(params)
            wf.writeframes(chunk1_frames)

        # Chunk 1 alone ("hey") does not trigger full wake word
        score1 = engine._score_acoustic_wake(chunk1_wav)
        assert score1 < 0.10, f"Expected chunk1 ('hey') score < 0.10, got {score1}"

        # When stitched across boundary (chunk1 + chunk2):
        combined_wav = os.path.join(tmpdir, "stitched.wav")
        with wave.open(combined_wav, "wb") as wf:
            wf.setparams(params)
            wf.writeframes(chunk1_frames + chunk2_frames)

        combined_score = engine._score_acoustic_wake(combined_wav)
        assert combined_score >= 0.85, f"Stitched chunk score was {combined_score}, expected >= 0.85"
