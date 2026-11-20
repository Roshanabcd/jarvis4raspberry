"""Minimal local daemon telemetry. Never contains transcripts or identity data."""
import json
import math
import os
from pathlib import Path
import tempfile
import time

STATES = frozenset({'DISABLED', 'STANDBY_LISTENING', 'WAKE_DETECTED', 'LISTENING_SPEECH',
                    'STREAMING_TRANSCRIPTION', 'SILENCE_COUNTDOWN', 'COMMAND_SUBMITTED',
                    'PROCESSING_AGENT', 'SPEAKING_RESPONSE', 'FOLLOW_UP_STANDBY', 'MUTED', 'ERROR'})


def status_path():
    return Path(f'/run/user/{os.getuid()}/jarvis/voice-status.json')


def _safe_diagnostics(data):
    """Allow only bounded, non-content health fields from the daemon."""
    if not isinstance(data, dict):
        return {}
    result = {}
    enums = {
        'capture_status': {'waiting', 'recording', 'ok', 'failed'},
        'capture_failure_reason': {'none', 'file_cleanup_failed', 'recorder_exit', 'empty_or_stale_file', 'recorder_exception'},
        'stt_status': {'idle', 'simulated', 'no_audio', 'silence', 'recognizing',
                       'recognized', 'unintelligible', 'loading_model', 'unavailable', 'failed'},
    }
    for key, values in enums.items():
        if isinstance(data.get(key), str) and data[key] in values:
            result[key] = data[key]
    for key in ('last_capture_age_s', 'audio_level_rms', 'energy_threshold_rms'):
        value = data.get(key)
        if value is None:
            result[key] = None
        elif type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1e9:
            result[key] = value
    if type(data.get('recorder_failures')) is int and 0 <= data['recorder_failures'] <= 1e9:
        result['recorder_failures'] = data['recorder_failures']
    if type(data.get('wake_word_enabled')) is bool:
        result['wake_word_enabled'] = data['wake_word_enabled']
    if type(data.get('recorder_exit_code')) is int and -128 <= data['recorder_exit_code'] <= 255:
        result['recorder_exit_code'] = data['recorder_exit_code']
    return result


def publish_status(state, running, *, path=None, diagnostics=None):
    path = Path(path) if path is not None else status_path()
    if state not in STATES or type(running) is not bool:
        raise ValueError('Invalid daemon telemetry')
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.voice-status-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump({'state': state, 'is_running': running, 'muted': state == 'MUTED',
                       'timestamp': time.time(), 'pid': os.getpid(),
                       **(_safe_diagnostics(diagnostics) if diagnostics is not None else {})}, stream)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_status(*, path=None, now=None):
    path = Path(path) if path is not None else status_path()
    try:
        with path.open() as stream:
            raw = stream.read(4097)
        if len(raw) > 4096:
            return None
        data = json.loads(raw)
        timestamp = data.get('timestamp')
        if type(timestamp) not in (int, float):
            return None
        age = (time.time() if now is None else now) - timestamp
        if not 0 <= age <= 10:
            return None
        if data.get('state') not in STATES or type(data.get('is_running')) is not bool:
            return None
        if type(data.get('pid')) is not int or data['pid'] <= 0:
            return None
        # Select fields explicitly; never forward arbitrary file content to the API.
        return {'state': data['state'], 'is_running': data['is_running'],
                'muted': data['state'] == 'MUTED', 'age_seconds': round(age, 1),
                **_safe_diagnostics(data)}
    except (OSError, ValueError, TypeError, AttributeError):
        return None
