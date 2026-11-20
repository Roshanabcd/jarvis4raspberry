import json
import threading
import wave
from unittest.mock import MagicMock

import pytest
import requests

from apps.voice.daemon_status import publish_status, read_status
from apps.voice.wake_word_engine import WakeState, WakeWordEngine


@pytest.mark.parametrize('failure', ['timeout', 'connection', 'http', 'invalid_json', 'empty_response', 'wrong_shape'])
def test_uncertain_backend_result_never_replays_action(monkeypatch, tmp_path, failure):
    engine = WakeWordEngine(temp_dir=str(tmp_path))
    handler = MagicMock()
    engine.set_command_handler(handler)
    identity = MagicMock(status_code=200)
    response = MagicMock(status_code=503 if failure == 'http' else 200)
    response.json.side_effect = ValueError('invalid response')
    if failure in {'empty_response', 'wrong_shape'}:
        response.json.side_effect = None
        response.json.return_value = {'response': '  '} if failure == 'empty_response' else []
    outcome = {'timeout': requests.ReadTimeout(), 'connection': requests.ConnectionError(),
               'http': response, 'invalid_json': response,
               'empty_response': response, 'wrong_shape': response}[failure]
    post = MagicMock(side_effect=[identity, outcome])
    monkeypatch.setattr('apps.voice.wake_word_engine.requests.post', post)
    brain = MagicMock()
    monkeypatch.setattr('ai.brain.get_brain', brain)
    engine._execute_command_and_respond('perform the requested action')
    assert post.call_count == 2
    handler.assert_not_called()
    brain.assert_not_called()
    assert 'could not be verified' in engine._last_error
    assert engine.state == WakeState.STANDBY_LISTENING


def test_confirmed_backend_response_enters_follow_up(monkeypatch, tmp_path):
    engine = WakeWordEngine(temp_dir=str(tmp_path))
    response = MagicMock(status_code=200)
    response.json.return_value = {'response': 'Completed once'}
    monkeypatch.setattr('apps.voice.wake_word_engine.requests.post', MagicMock(return_value=response))
    engine._execute_command_and_respond('a harmless command')
    assert engine._last_response == 'Completed once'
    assert engine._last_error is None
    assert engine.state == WakeState.FOLLOW_UP_STANDBY


def test_telemetry_contains_no_transcript_or_identity(tmp_path):
    path = tmp_path / 'status.json'
    publish_status('STANDBY_LISTENING', True, path=path)
    raw = json.loads(path.read_text())
    assert set(raw) == {'state', 'is_running', 'muted', 'timestamp', 'pid'}
    assert path.stat().st_mode & 0o777 == 0o600
    assert read_status(path=path)['state'] == 'STANDBY_LISTENING'
    assert read_status(path=path, now=raw['timestamp'] + 11) is None
    assert read_status(path=path, now=raw['timestamp'] - 1) is None


@pytest.mark.parametrize('payload', ['broken json', '[]', '{"state": "fake"}', 'x' * 4097])
def test_invalid_telemetry_is_ignored(tmp_path, payload):
    path = tmp_path / 'status.json'
    path.write_text(payload)
    assert read_status(path=path) is None


def test_voice_api_uses_daemon_state_instead_of_idle_backend(monkeypatch):
    from apps.api.voice_api import get_voice_status, voice_service
    from apps.voice.speech_manager import speech_manager
    monkeypatch.setattr(voice_service, 'get_state', lambda: {'state': 'DISABLED', 'listening': False})
    monkeypatch.setattr(speech_manager, 'get_status', lambda: {'speaker': {}, 'tts': {}})
    monkeypatch.setattr('apps.voice.wake_word_engine.is_voice_service_daemon_running', lambda: True)
    monkeypatch.setattr('apps.voice.daemon_status.read_status', lambda: {'state': 'MUTED', 'is_running': True, 'muted': True})
    status = get_voice_status()
    assert status['state'] == 'MUTED'
    assert status['capture_owner'] == 'voice_daemon'
    assert status['listening'] is False
    assert status['local_state'] == 'DISABLED'


@pytest.mark.parametrize('state,listening', [('STANDBY_LISTENING', True), ('PROCESSING_AGENT', False), ('DISABLED', False)])
def test_daemon_listening_status_matches_state(monkeypatch, state, listening):
    from apps.api import voice_api
    monkeypatch.setattr(voice_api.voice_service, 'get_state', lambda: {'state': 'DISABLED'})
    monkeypatch.setattr('apps.voice.speech_manager.speech_manager.get_status', lambda: {'speaker': {}, 'tts': {}})
    telemetry = {'state': state, 'is_running': state != 'DISABLED', 'muted': False}
    monkeypatch.setattr(voice_api, '_daemon_snapshot', lambda: (True, telemetry))
    assert voice_api.get_voice_status()['listening'] is listening
    assert voice_api.get_wake_word_status()['state'] == state


@pytest.mark.parametrize('owner', [True, None])
def test_unavailable_daemon_telemetry_never_reports_local_state(monkeypatch, owner):
    from apps.api import voice_api
    monkeypatch.setattr(voice_api.voice_service, 'get_state', lambda: {'state': 'DISABLED'})
    monkeypatch.setattr('apps.voice.speech_manager.speech_manager.get_status', lambda: {'speaker': {}, 'tts': {}})
    monkeypatch.setattr(voice_api, '_daemon_snapshot', lambda: (owner, None))
    assert voice_api.get_voice_status()['listening'] is None
    wake = voice_api.get_wake_word_status()
    assert wake['state'] == 'EXTERNAL_OWNER'
    assert wake['telemetry_available'] is False


def test_wake_status_preserves_backend_owner(monkeypatch):
    from apps.api import voice_api
    monkeypatch.setattr(voice_api, '_daemon_snapshot', lambda: (False, None))
    expected = {'state': 'MUTED', 'is_running': True}
    monkeypatch.setattr('apps.voice.wake_word_engine.wake_word_engine.get_status', lambda: expected)
    assert voice_api.get_wake_word_status() == expected


def test_recording_removes_stale_file_and_rejects_failed_recorder(monkeypatch, tmp_path):
    output = tmp_path / "chunk.wav"
    output.write_bytes(b"stale audio")
    proc = MagicMock()
    proc.poll.return_value = None
    proc.returncode = 1
    proc.communicate.return_value = ("", "")
    proc.terminate.return_value = None
    monkeypatch.setattr("apps.voice.wake_word_engine.subprocess.Popen", lambda *args, **kwargs: proc)
    monkeypatch.setattr("apps.voice.wake_word_engine.time.sleep", lambda _: None)

    engine = WakeWordEngine(temp_dir=str(tmp_path))
    assert engine._record_audio_chunk(str(output), duration_s=0) is False
    assert not output.exists()


def test_stop_from_daemon_loop_does_not_join_itself(tmp_path):
    engine = WakeWordEngine(temp_dir=str(tmp_path))
    engine._is_running = True
    engine._thread = threading.current_thread()

    engine.stop()

    assert engine.state == WakeState.DISABLED
    assert engine._thread is None


def test_rms_handles_stereo_wav(tmp_path):
    path = tmp_path / "stereo.wav"
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x10\x00\x10\x00" * 100)

    engine = WakeWordEngine(temp_dir=str(tmp_path))
    assert engine._calculate_audio_rms(str(path)) == pytest.approx(16.0)


def test_cross_process_daemon_control(tmp_path):
    from apps.voice.daemon_control import send_daemon_command, poll_daemon_command
    ctrl_path = tmp_path / "voice-control.json"

    # Send mute command
    assert send_daemon_command("mute", path=ctrl_path)
    cmd = poll_daemon_command(path=ctrl_path)
    assert cmd == "mute"
    # Command should be consumed
    assert poll_daemon_command(path=ctrl_path) is None

    # Test unknown action rejected
    assert not send_daemon_command("invalid_action", path=ctrl_path)


def test_missing_audio_device_reports_unavailable_without_fake_hardware(monkeypatch):
    from apps.voice.audio_manager import AudioManager

    class Result:
        returncode = 1
        stdout = ""
        stderr = "no cards found"

    monkeypatch.setattr("apps.voice.audio_manager.subprocess.run", lambda *args, **kwargs: Result())
    manager = AudioManager(simulation_mode=False)

    assert manager.detect_devices() == [{"card": 0, "device": 0, "name": "Simulated"}]
    assert manager.is_microphone_available() is False


def test_cross_process_speaker_feedback_guard(tmp_path):
    from apps.voice.playback_state import set_playback_active, is_playback_active
    from apps.voice.wake_word_engine import WakeWordEngine
    state_path = tmp_path / "playback-active.json"

    engine = WakeWordEngine(temp_dir=str(tmp_path))
    # Initially not playing
    assert not is_playback_active(path=state_path)
    assert not engine._is_tts_playing(playback_path=state_path)

    # Core starts playing audio
    set_playback_active(True, path=state_path)
    assert is_playback_active(path=state_path)
    assert engine._is_tts_playing(playback_path=state_path)

    # Core finishes playing audio
    set_playback_active(False, path=state_path)
    assert not is_playback_active(path=state_path)
    assert not engine._is_tts_playing(playback_path=state_path)


def test_stale_playback_monitor_cannot_clear_newer_lease(tmp_path):
    from apps.voice.playback_state import is_playback_active, set_playback_active
    state_path = tmp_path / "playback-active.json"

    assert set_playback_active(True, path=state_path, lease_id="old")
    assert set_playback_active(True, path=state_path, lease_id="new")
    assert set_playback_active(False, path=state_path, lease_id="old")
    assert is_playback_active(path=state_path)

    assert set_playback_active(False, path=state_path, lease_id="new")
    assert not is_playback_active(path=state_path)


def test_pw_record_backoff_on_repeated_failure(monkeypatch, tmp_path):
    from apps.voice.wake_word_engine import WakeWordEngine
    output = tmp_path / "chunk.wav"
    proc = MagicMock()
    proc.poll.return_value = None
    proc.returncode = 1
    proc.communicate.return_value = ("", "")
    monkeypatch.setattr("apps.voice.wake_word_engine.subprocess.Popen", lambda *args, **kwargs: proc)
    monkeypatch.setattr("apps.voice.wake_word_engine.time.sleep", lambda _: None)

    engine = WakeWordEngine(temp_dir=str(tmp_path))
    assert engine._recorder_consecutive_failures == 0
    engine._record_audio_chunk(str(output), duration_s=0)
    assert engine._recorder_consecutive_failures == 1
    engine._record_audio_chunk(str(output), duration_s=0)
    assert engine._recorder_consecutive_failures == 2
    delay = engine._get_recorder_backoff_delay()
    assert delay > 0.5


def test_voice_jobs_lifecycle_and_cancellation():
    from apps.voice.voice_jobs import VoiceJobManager
    mgr = VoiceJobManager()
    job = mgr.create_job("Hello from JARVIS")
    assert job.status == "queued"
    assert job.text == "Hello from JARVIS"

    mgr.update_job(job.job_id, status="synthesizing", provider="local_tts")
    fetched = mgr.get_job(job.job_id)
    assert fetched.status == "synthesizing"
    assert fetched.provider == "local_tts"

    mgr.cancel_active_jobs()
    fetched_after = mgr.get_job(job.job_id)
    assert fetched_after.status == "cancelled"


def test_voice_jobs_are_bounded_and_validate_updates():
    from apps.voice.voice_jobs import VoiceJobManager

    mgr = VoiceJobManager(max_history=2)
    first = mgr.create_job("first")
    second = mgr.create_job("second")
    third = mgr.create_job("third")

    assert mgr.get_job(first.job_id) is None
    assert [job.job_id for job in mgr.list_jobs(limit=10)] == [third.job_id, second.job_id]

    with pytest.raises(ValueError, match="Unknown voice job field"):
        mgr.update_job(second.job_id, unexpected="value")
    with pytest.raises(ValueError, match="Invalid voice job status"):
        mgr.update_job(second.job_id, status="unknown")


def test_voice_job_manager_rejects_empty_history_limit():
    from apps.voice.voice_jobs import VoiceJobManager

    with pytest.raises(ValueError, match="max_history"):
        VoiceJobManager(max_history=0)


def test_voice_api_reports_daemon_dispatch_failure(monkeypatch):
    from apps.api import voice_api
    from fastapi import HTTPException

    monkeypatch.setattr(
        voice_api,
        "_daemon_snapshot",
        lambda: (True, {"state": "STANDBY_LISTENING", "is_running": True, "muted": False}),
    )
    monkeypatch.setattr("apps.voice.daemon_control.send_daemon_command", lambda action: False)

    with pytest.raises(HTTPException) as exc_info:
        voice_api.mute_voice()
    assert exc_info.value.status_code == 503


def test_voice_api_mute_unmute_stop_targets_daemon_when_active(monkeypatch):
    from apps.api import voice_api
    daemon_cmds = []
    monkeypatch.setattr(voice_api, "_daemon_snapshot", lambda: (True, {"state": "STANDBY_LISTENING", "is_running": True, "muted": False}))
    monkeypatch.setattr("apps.voice.daemon_control.send_daemon_command", lambda action: daemon_cmds.append(action) or True)

    voice_api.mute_voice()
    assert daemon_cmds == ["mute"]

    voice_api.unmute_voice()
    assert daemon_cmds == ["mute", "unmute"]

    voice_api.stop_voice_listening()
    assert daemon_cmds == ["mute", "unmute", "stop"]

