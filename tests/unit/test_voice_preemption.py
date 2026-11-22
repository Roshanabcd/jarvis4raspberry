import queue
import threading
from unittest.mock import MagicMock, patch
import pytest

from apps.voice.service import VoiceService
from apps.voice.voice_jobs import VoiceJobManager, VoiceJob


def make_service(manager, capacity=4):
    service = VoiceService.__new__(VoiceService)
    service._job_manager = manager
    service._reply_queue = queue.Queue(maxsize=capacity)
    service._reply_enqueue_lock = threading.Lock()
    service._delivery_stop = threading.Event()
    service._last_staged = {}
    service._speech_generation = 0
    service._ensure_delivery_worker = lambda: None
    return service


def test_stop_playback_advances_generation_and_flushes_queue():
    manager = VoiceJobManager(max_history=10)
    service = make_service(manager, capacity=4)

    job1 = service.enqueue_response("first speech")
    job2 = service.enqueue_response("second speech")
    assert service._reply_queue.qsize() == 2
    initial_gen = service._speech_generation

    with patch("apps.voice.speech_manager.speech_manager.stop") as mock_stop:
        service.stop_playback()
        mock_stop.assert_called_once()

    assert service._speech_generation == initial_gen + 1
    assert service._reply_queue.empty()
    assert manager.get_job(job1.job_id).status == "cancelled"
    assert manager.get_job(job2.job_id).status == "cancelled"


def test_preemption_drops_stale_job_with_older_generation():
    manager = VoiceJobManager(max_history=10)
    service = make_service(manager, capacity=4)

    # Job created at generation 0
    job = manager.create_job("stale reply", generation=0)

    # Advanced generation to 1
    service._speech_generation = 1

    synth_called = False

    class DummySpeech:
        def synthesize_and_stage(self, text, play_system=False):
            nonlocal synth_called
            synth_called = True
            return {"status": "ok", "success": True, "audio_id": "a1"}

        def get_staged_audio(self, audio_id):
            return ("a1.wav", "audio/wav")

        def play_system_audio(self, *args, **kwargs):
            return True

    with patch("apps.voice.speech_manager.speech_manager", DummySpeech()):
        result = service.process_one_job(job)

    assert not synth_called
    assert result.status == "cancelled"
    assert "Preempted" in (result.error or "")


def test_preemption_drops_synthesized_audio_if_generation_advanced_during_synthesis():
    manager = VoiceJobManager(max_history=10)
    service = make_service(manager, capacity=4)

    job = manager.create_job("reply", generation=0)
    service._speech_generation = 0

    playback_called = False

    class AdvancingSpeech:
        def synthesize_and_stage(self, text, play_system=False):
            # Simulate preemption occurring while synthesis was in flight
            service._speech_generation = 1
            return {
                "status": "ok",
                "success": True,
                "audio_id": "audio-staged-1",
                "audio_url": "/api/voice/audio/audio-staged-1",
                "provider": "edge_tts",
            }

        def get_staged_audio(self, audio_id):
            return ("audio.wav", "audio/wav")

        def play_system_audio(self, *args, **kwargs):
            nonlocal playback_called
            playback_called = True
            return True

    with patch("apps.voice.speech_manager.speech_manager", AdvancingSpeech()):
        result = service.process_one_job(job)

    assert not playback_called
    assert result.status == "cancelled"
    assert "Preempted" in (result.error or "")


def test_message_two_interrupts_message_one_and_plays_only_two():
    manager = VoiceJobManager(max_history=10)
    service = make_service(manager, capacity=4)

    job1 = service.enqueue_response("message one")
    assert getattr(job1, "generation", 0) == 0

    # User barges in with message two
    service.stop_playback()
    assert service._speech_generation == 1

    job2 = service.enqueue_response("message two")
    assert getattr(job2, "generation", 0) == 1

    played_jobs = []

    class MockSpeech:
        def synthesize_and_stage(self, text, play_system=False):
            return {
                "status": "ok",
                "success": True,
                "audio_id": f"audio-{text}",
                "audio_url": f"/api/voice/audio/{text}",
                "provider": "edge_tts",
            }

        def get_staged_audio(self, audio_id):
            return (f"{audio_id}.wav", "audio/wav")

        def play_system_audio(self, path, wait=True, playback_owner=None, should_play=None):
            if should_play and not should_play():
                return False
            played_jobs.append(playback_owner)
            return True

    with patch("apps.voice.speech_manager.speech_manager", MockSpeech()):
        # Try to process stale job1
        res1 = service.process_one_job(job1)
        # Process active job2
        res2 = service.process_one_job(job2)

    assert res1.status == "cancelled"
    assert res2.status == "completed"
    assert played_jobs == [job2.job_id]
