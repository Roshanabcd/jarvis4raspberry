"""Capture-owner regressions using synthetic audio and mocked recognition only."""
import json
import struct
import sys
import time
import types
import wave
from unittest.mock import MagicMock

import pytest

from apps.voice.daemon_status import publish_status, read_status
from apps.voice.stt import SpeechToText
from apps.voice.wake_word_engine import WakeState, WakeWordEngine


@pytest.mark.parametrize('phrase,command', [
    ('Hey Jarvis, what time is it?', 'what time is it?'),
    ('WAKE UP JARVIS: help me', 'help me'),
    ('Jarvis!', ''),
    ('unrelated words', ''),
])
def test_command_after_wake_phrase_is_preserved(tmp_path, phrase, command):
    engine = WakeWordEngine(temp_dir=str(tmp_path))
    assert engine._command_after_wake_phrase(phrase) == command


def test_inline_wake_command_reaches_backend_once(monkeypatch, tmp_path):
    engine = WakeWordEngine(temp_dir=str(tmp_path))
    engine._is_running = True
    engine.set_state(WakeState.STANDBY_LISTENING)
    monkeypatch.setattr(engine, '_check_daemon_commands', lambda: None)
    monkeypatch.setattr(engine, '_is_tts_playing', lambda: False)
    monkeypatch.setattr(engine, '_record_audio_chunk', lambda *a, **kw: True)
    monkeypatch.setattr(engine, '_calculate_audio_rms', MagicMock(side_effect=[500, 0]))
    monkeypatch.setattr(engine, '_transcribe', lambda _: 'Hey Jarvis, what time is it?')
    # Synthetic silence finalizes immediately, without sleeping or device access.
    engine.silence_timeout_s = 0
    commands = []
    def execute(text):
        commands.append(text)
        engine.stop()
    monkeypatch.setattr(engine, '_execute_command_and_respond', execute)
    engine._run_loop()
    assert commands == ['what time is it?']


def test_mute_is_consumed_inside_listening_loop(monkeypatch, tmp_path):
    engine = WakeWordEngine(temp_dir=str(tmp_path))
    engine._is_running = True
    engine.set_state(WakeState.LISTENING_SPEECH)
    recorder = MagicMock()
    monkeypatch.setattr(engine, '_record_audio_chunk', recorder)
    monkeypatch.setattr(engine, '_is_tts_playing', lambda: False)
    calls = []
    def commands():
        calls.append(True)
        if len(calls) == 2:
            engine.mute()
        if len(calls) == 3:
            assert engine.state == WakeState.MUTED
            engine.stop()
    monkeypatch.setattr(engine, '_check_daemon_commands', commands)
    engine._run_loop()
    recorder.assert_not_called()
    assert len(calls) == 3


def test_capture_health_roundtrip_excludes_private_or_unvalidated_fields(tmp_path):
    target = tmp_path / 'telemetry.json'
    publish_status('STANDBY_LISTENING', True, path=target, diagnostics={
        'capture_status': 'failed', 'recorder_failures': 3, 'audio_level_rms': 12,
        'energy_threshold_rms': 90, 'last_capture_age_s': 2.5,
        'stt_status': 'unavailable', 'wake_word_enabled': True,
        'transcript': 'private text', 'error': 'private provider payload',
    })
    status = read_status(path=target)
    assert status['capture_status'] == 'failed'
    assert status['recorder_failures'] == 3
    assert status['stt_status'] == 'unavailable'
    assert 'private' not in target.read_text()
    raw = json.loads(target.read_text())
    raw.update(audio_level_rms=float('nan'), recorder_failures=True, stt_status='private content')
    target.write_text(json.dumps(raw))
    status = read_status(path=target)
    assert 'audio_level_rms' not in status
    assert 'recorder_failures' not in status
    assert 'stt_status' not in status


def test_capture_diagnostics_do_not_initialize_recognizer(tmp_path):
    engine = WakeWordEngine(temp_dir=str(tmp_path))
    engine._last_capture_time = time.monotonic() - 3
    engine._last_audio_rms = 25
    engine._capture_status = 'ok'
    status = engine.get_capture_diagnostics()
    assert status['last_capture_age_s'] >= 3
    assert status['audio_level_rms'] == 25
    assert status['stt_status'] == 'idle'
    assert engine._stt is None


def test_recognition_network_timeout_and_private_logging(monkeypatch, tmp_path, caplog):
    audio = tmp_path / 'synthetic.wav'
    with wave.open(str(audio), 'wb') as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(16000)
        stream.writeframes(struct.pack('<h', 100) * 100)
    recognizer = MagicMock()
    recognizer.recognize_google.return_value = 'private test transcript'
    module = types.SimpleNamespace(
        Recognizer=lambda: recognizer, AudioFile=MagicMock(),
        UnknownValueError=type('UnknownValueError', (Exception,), {}),
        RequestError=type('RequestError', (Exception,), {}),
    )
    monkeypatch.setitem(sys.modules, 'speech_recognition', module)
    stt = SpeechToText(simulation_mode=False)
    with caplog.at_level('INFO'):
        assert stt.transcribe(str(audio)) == 'private test transcript'
    assert recognizer.operation_timeout == 8.0
    assert stt.last_status == 'recognized'
    assert 'private test transcript' not in caplog.text


@pytest.mark.parametrize('running,valid,expected', [(True,True,True),(False,True,False),(True,False,False)])
def test_expected_pipewire_signal_exit_requires_valid_complete_audio(monkeypatch, tmp_path, running, valid, expected):
    output = tmp_path / 'capture.wav'
    proc = MagicMock()
    proc.poll.return_value = None if running else 1
    proc.returncode = 1
    def finish(**kwargs):
        if valid:
            with wave.open(str(output),'wb') as audio:
                audio.setnchannels(1); audio.setsampwidth(2); audio.setframerate(16000)
                audio.writeframes(b'\x00\x00' * 16000)
        else:
            output.write_bytes(b'invalid' * 100)
        return b'', b''
    proc.communicate.side_effect = finish
    monkeypatch.setattr('apps.voice.wake_word_engine.subprocess.Popen', lambda *a, **kw: proc)
    monkeypatch.setattr('apps.voice.wake_word_engine.time.sleep', lambda _: None)
    engine = WakeWordEngine(temp_dir=str(tmp_path))
    assert engine._record_audio_chunk(str(output), duration_s=0.1) is expected
    assert engine.get_capture_diagnostics()['capture_status'] == ('ok' if expected else 'failed')
