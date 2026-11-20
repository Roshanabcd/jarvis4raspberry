import queue
import threading
from unittest.mock import MagicMock, patch

import pytest

from apps.voice.service import VoiceService
from apps.voice.voice_jobs import VoiceJobManager


def delivery_service(manager, capacity=2):
    service = VoiceService.__new__(VoiceService)
    service._job_manager = manager
    service._reply_queue = queue.Queue(maxsize=capacity)
    service._reply_enqueue_lock = threading.Lock()
    service._delivery_stop = threading.Event()
    service._last_staged = {}
    service._ensure_delivery_worker = lambda: None
    return service


def test_terminal_job_cannot_be_resurrected():
    manager = VoiceJobManager(max_history=4)
    job = manager.create_job("hello")
    manager.update_job(job.job_id, status="failed", error="broken")

    manager.update_job(job.job_id, status="playing")
    current = manager.get_job(job.job_id)

    assert current.status == "failed"
    assert current.error == "broken"


def test_enqueue_refuses_capacity_without_creating_an_untracked_job():
    manager = VoiceJobManager(max_history=4)
    service = delivery_service(manager, capacity=1)
    first = service.enqueue_response("first")

    with pytest.raises(RuntimeError, match="full"):
        service.enqueue_response("second")

    assert manager.get_job(first.job_id).status == "queued"
    assert len(manager.list_jobs(10)) == 1


def test_cancellation_during_synthesis_prevents_playback():
    manager = VoiceJobManager(max_history=4)
    service = delivery_service(manager)
    job = service.enqueue_response("hello")
    synthesis_started = threading.Event()
    release_synthesis = threading.Event()

    class Speech:
        def synthesize_and_stage(self, text, play_system=False):
            synthesis_started.set()
            release_synthesis.wait(2)
            return {
                "status": "ok",
                "success": True,
                "audio_id": "audio-1",
                "provider": "test",
            }

        def get_staged_audio(self, audio_id):
            return ("audio.wav", "audio/wav")

        def play_system_audio(self, *args, **kwargs):
            raise AssertionError("cancelled job must not start playback")

    with patch("apps.voice.speech_manager.speech_manager", Speech()):
        worker = threading.Thread(target=service.process_one_job, args=(job,))
        worker.start()
        assert synthesis_started.wait(2)
        service.cancel_response(job.job_id)
        release_synthesis.set()
        worker.join(2)

    assert manager.get_job(job.job_id).status == "cancelled"


def test_cancellation_during_playback_cannot_complete_job():
    manager = VoiceJobManager(max_history=4)
    service = delivery_service(manager)
    job = service.enqueue_response("hello")
    playback_started = threading.Event()
    release_playback = threading.Event()

    class Speech:
        def synthesize_and_stage(self, text, play_system=False):
            return {
                "status": "ok",
                "success": True,
                "audio_id": "audio-1",
                "provider": "test",
            }

        def get_staged_audio(self, audio_id):
            return ("audio.wav", "audio/wav")

        def play_system_audio(self, path, wait=True, should_play=None, playback_owner=None):
            playback_started.set()
            release_playback.wait(2)
            return False

        def stop(self, **kwargs):
            release_playback.set()

    with patch("apps.voice.speech_manager.speech_manager", Speech()):
        worker = threading.Thread(target=service.process_one_job, args=(job,))
        worker.start()
        assert playback_started.wait(2)
        service.cancel_response(job.job_id)
        worker.join(2)

    assert manager.get_job(job.job_id).status == "cancelled"


@pytest.mark.parametrize('staged', [None, [], {'status': 'error', 'error': 'provider failed'},
                                     {'status': 'ok', 'success': True}])
def test_synthesis_failure_is_terminal_without_fallback(staged):
    manager = VoiceJobManager()
    service = delivery_service(manager)
    service.tts = MagicMock()
    speech = MagicMock()
    speech.synthesize_and_stage.return_value = staged
    job = service.enqueue_response('reply')
    with patch('apps.voice.speech_manager.speech_manager', speech):
        result = service.process_one_job(job)
    assert result.status == 'failed'
    assert result.error
    speech.play_system_audio.assert_not_called()
    service.tts.speak_sync.assert_not_called()
    assert service._last_staged == {}


@pytest.mark.parametrize('played,expected', [(True, 'completed'), (False, 'failed')])
def test_delivery_completes_only_after_successful_playback(played, expected):
    manager = VoiceJobManager()
    service = delivery_service(manager)
    speech = MagicMock()
    speech.synthesize_and_stage.return_value = {'status': 'ok', 'success': True,
                                               'audio_id': 'audio-1', 'audio_url': '/audio/1'}
    speech.get_staged_audio.return_value = ('fake.wav', 'audio/wav')
    speech.play_system_audio.return_value = played
    job = service.enqueue_response('reply')
    with patch('apps.voice.speech_manager.speech_manager', speech):
        result = service.process_one_job(job)
    assert result.status == expected
    speech.synthesize_and_stage.assert_called_once_with('reply', play_system=False)
    assert speech.play_system_audio.call_args.kwargs['wait'] is True


def test_protected_history_never_evicts_active_jobs():
    manager = VoiceJobManager(max_history=1)
    first = manager.create_job('first', preserve_active=True)
    with pytest.raises(RuntimeError, match='full'):
        manager.create_job('second', preserve_active=True)
    manager.update_job(first.job_id, status='failed')
    second = manager.create_job('second', preserve_active=True)
    assert manager.get_job(first.job_id) is None
    assert manager.get_job(second.job_id).status == 'queued'


def test_invalid_update_is_atomic():
    manager = VoiceJobManager()
    job = manager.create_job('reply')
    with pytest.raises(ValueError):
        manager.update_job(job.job_id, status='synthesizing', latency_ms='invalid')
    assert manager.get_job(job.job_id).status == 'queued'
    with pytest.raises(ValueError, match='Immutable'):
        manager.update_job(job.job_id, created_at=0)


def test_command_queues_one_reply_without_background_duplicates(monkeypatch):
    from fastapi import BackgroundTasks
    from apps.api import voice_api
    job = VoiceJobManager().create_job('reply')
    process = MagicMock(return_value='reply')
    enqueue = MagicMock(return_value=job)
    monkeypatch.setattr(voice_api.voice_service, 'process_command', process)
    monkeypatch.setattr(voice_api.voice_service, 'enqueue_response', enqueue)
    tasks = BackgroundTasks()
    result = voice_api.run_command(voice_api.CommandRequest(text='request'), tasks)
    process.assert_called_once_with('request', speak=False)
    enqueue.assert_called_once_with('reply', broadcast=False)
    assert result['job_id'] == job.job_id
    assert tasks.tasks == []


def test_command_queue_rejection_keeps_confirmed_inference_response(monkeypatch):
    from apps.api import voice_api
    process = MagicMock(return_value='action already completed')
    monkeypatch.setattr(voice_api.voice_service, 'process_command', process)
    monkeypatch.setattr(voice_api.voice_service, 'enqueue_response', MagicMock(side_effect=RuntimeError('queue full')))
    result = voice_api.run_command(voice_api.CommandRequest(text='request'))
    assert result['response'] == 'action already completed'
    assert result['job_status'] == 'rejected'
    assert result['audio_error'] == 'queue full'
    process.assert_called_once()


@pytest.fixture
def playback_manager(monkeypatch, tmp_path):
    from types import SimpleNamespace
    from apps.voice import speech_manager as module
    manager = module.SpeechOutputManager(stage_dir=str(tmp_path))
    audio_path = tmp_path / 'reply.wav'
    audio_path.write_bytes(b'RIFF' + b'\0' * 40)
    monkeypatch.setattr(module.shutil, 'which', lambda _: '/mock/player')
    monkeypatch.setattr(module.gradio_cloner, 'stop_playback', lambda: None)
    monkeypatch.setattr('apps.voice.playback_state.set_playback_active', lambda *args, **kwargs: True)
    monkeypatch.setattr('tools.media.audio_stream_manager.audio_stream_manager.duck_active_streams', lambda **kwargs: None)
    monkeypatch.setattr('tools.media.audio_stream_manager.audio_stream_manager.restore_active_streams', lambda: None)
    monkeypatch.setattr(module, 'threading', SimpleNamespace(Thread=lambda **kwargs: MagicMock()))
    return module, manager, str(audio_path)


@pytest.mark.parametrize('exit_code,expected', [(0, True), (2, False)])
def test_playback_wait_reports_actual_process_exit(playback_manager, monkeypatch, exit_code, expected):
    module, manager, audio_path = playback_manager
    process = MagicMock()
    process.wait.return_value = exit_code
    monkeypatch.setattr(module.subprocess, 'Popen', lambda *args, **kwargs: process)
    assert manager.play_system_audio(audio_path, wait=True) is expected
    assert manager._last_playback['status'] == ('completed' if expected else 'error')


def test_playback_wait_releases_lock_for_barge_in(playback_manager, monkeypatch):
    import concurrent.futures
    module, manager, audio_path = playback_manager
    process = MagicMock()
    process.poll.return_value = None
    waiting = threading.Event()
    stopped = threading.Event()
    process.terminate.side_effect = stopped.set

    def wait(timeout=None):
        if timeout == 180:
            waiting.set()
            assert stopped.wait(2), 'stop() blocked by playback wait lock'
        return -15

    process.wait.side_effect = wait
    monkeypatch.setattr(module.subprocess, 'Popen', lambda *args, **kwargs: process)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        result = pool.submit(manager.play_system_audio, audio_path, True)
        assert waiting.wait(2)
        pool.submit(manager.stop).result(timeout=2)
        assert result.result(timeout=2) is False


def test_playback_timeout_terminates_owned_player(playback_manager, monkeypatch):
    module, manager, audio_path = playback_manager
    process = MagicMock()
    process.poll.return_value = None
    process.wait.side_effect = [module.subprocess.TimeoutExpired('player', 15), -15]
    monkeypatch.setattr(module.subprocess, 'Popen', lambda *args, **kwargs: process)
    assert manager.play_system_audio(audio_path, wait=True) is False
    process.terminate.assert_called_once()
    assert manager._current_player is None
    assert manager._last_playback['status'] == 'error'


def test_cancelled_playback_guard_never_launches_player(playback_manager, monkeypatch):
    module, manager, audio_path = playback_manager
    launch = MagicMock()
    monkeypatch.setattr(module.subprocess, 'Popen', launch)
    assert manager.play_system_audio(audio_path, wait=True, should_play=lambda: False) is False
    launch.assert_not_called()


def test_cancelling_old_job_does_not_stop_newer_player(playback_manager, monkeypatch):
    module, manager, audio_path = playback_manager
    process = MagicMock()
    process.poll.return_value = None
    monkeypatch.setattr(module.subprocess, 'Popen', lambda *args, **kwargs: process)
    assert manager.play_system_audio(audio_path, playback_owner='new-job')
    manager.stop(expected_owner='old-job')
    process.terminate.assert_not_called()
    assert manager._current_player is process
    manager.stop(expected_owner='new-job')
    process.terminate.assert_called_once()


def test_job_snapshots_cannot_mutate_registry():
    manager = VoiceJobManager()
    job = manager.create_job('reply')
    job.status = 'completed'
    assert manager.get_job(job.job_id).status == 'queued'
    manager.update_job(job.job_id, status='cancelled')
    snapshot = manager.get_job(job.job_id)
    snapshot.status = 'playing'
    assert manager.get_job(job.job_id).status == 'cancelled'


def test_lazy_worker_is_single_and_serializes_reply_delivery():
    manager = VoiceJobManager()
    service = delivery_service(manager)
    del service._ensure_delivery_worker
    service._delivery_worker = None
    synthesis_entered = threading.Event()
    release = threading.Event()
    speech = MagicMock()
    calls = []

    def synthesize(text, play_system=False):
        calls.append(text)
        synthesis_entered.set()
        assert release.wait(2)
        return {'status': 'ok', 'success': True, 'audio_id': text}

    speech.synthesize_and_stage.side_effect = synthesize
    speech.get_staged_audio.return_value = ('fake.wav', 'audio/wav')
    speech.play_system_audio.return_value = True
    with patch('apps.voice.speech_manager.speech_manager', speech):
        first = service.enqueue_response('first')
        assert synthesis_entered.wait(2)
        worker = service._delivery_worker
        second = service.enqueue_response('second')
        assert service._delivery_worker is worker
        assert calls == ['first']
        release.set()
        service._reply_queue.join()
        service._delivery_stop.set()
        worker.join(2)
    assert calls == ['first', 'second']
    assert manager.get_job(first.job_id).status == 'completed'
    assert manager.get_job(second.job_id).status == 'completed'


@pytest.mark.parametrize('wait', [True, False])
def test_long_wav_reply_gets_duration_based_wait_allowance(playback_manager, monkeypatch, wait):
    module, manager, audio_path = playback_manager
    process = MagicMock()
    process.wait.return_value = 0
    monkeypatch.setattr(module.subprocess, 'Popen', lambda *args, **kwargs: process)
    audio = MagicMock()
    audio.__enter__.return_value = audio
    audio.getnframes.return_value = 48000 * 45
    audio.getframerate.return_value = 48000
    monkeypatch.setattr(module.wave, 'open', lambda *args: audio)
    publish = MagicMock()
    monkeypatch.setattr('apps.voice.playback_state.set_playback_active', publish)
    assert manager.play_system_audio(audio_path, wait=wait) is True
    active_leases = [call for call in publish.call_args_list if call.args == (True,)]
    assert len(active_leases) == 1
    assert active_leases[0].kwargs['duration_hint_s'] == 55.0
    if wait:
        process.wait.assert_called_once_with(timeout=55.0)
    else:
        process.wait.assert_not_called()


def test_long_reply_renews_capture_pause_only_while_it_owns_player(playback_manager, monkeypatch):
    module, manager, audio_path = playback_manager
    process = MagicMock()
    process.poll.return_value = None
    process.wait.side_effect = [module.subprocess.TimeoutExpired('player', 10), 0]
    monkeypatch.setattr(module.subprocess, 'Popen', lambda *args, **kwargs: process)
    monitor = {}

    def thread(**kwargs):
        monitor.update(kwargs)
        return MagicMock()

    monkeypatch.setattr(module.threading, 'Thread', thread)
    publish = MagicMock()
    monkeypatch.setattr('apps.voice.playback_state.set_playback_active', publish)
    assert manager.play_system_audio(audio_path, playback_owner='reply') is True
    monitor['target'](*monitor['args'])
    active = [call for call in publish.call_args_list if call.args == (True,)]
    assert len(active) == 2  # Initial lease and a renewal after ten seconds.
    assert active[0].kwargs['lease_id'] == active[1].kwargs['lease_id']

    publish.reset_mock()
    process.wait.side_effect = [module.subprocess.TimeoutExpired('player', 10)]
    manager._current_player = object()  # A later reply now owns playback.
    monitor['target'](*monitor['args'])
    assert not [call for call in publish.call_args_list if call.args == (True,)]
