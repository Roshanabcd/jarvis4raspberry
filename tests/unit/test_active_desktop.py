"""No device capture: test leases, local API boundaries, and memory-only frames."""
import io
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from apps.core.app_factory import create_app, noop_lifespan
from apps.desktop.active_session import ActiveDesktopSession, VoiceLease
from apps.api import active_desktop_api as api


@pytest.fixture
def session(monkeypatch):
    clock = [100.0]
    voice = MagicMock()
    voice.start.return_value = {"state": "listening"}
    session = ActiveDesktopSession(voice_factory=lambda: voice, clock=lambda: clock[0])
    # Drive expiry explicitly rather than starting long-lived threads in tests.
    monkeypatch.setattr(session, '_watch', lambda: None)
    yield session, clock, voice
    if session._token:
        session.stop(session._token)


def frame_bytes(size=(80, 40)):
    data = io.BytesIO()
    Image.new('RGB', size, 'blue').save(data, 'PNG')
    return data.getvalue()


def test_expiry_restores_voice_and_purges_frame(session):
    manager, clock, voice = session
    token = manager.start()['token']
    manager.frame(token, frame_bytes())
    assert manager.status()['screen'] == 'receiving'
    clock[0] += 31
    assert manager.status()['active'] is False
    assert manager._frame is None
    voice.stop.assert_called_once()
    with pytest.raises(PermissionError): manager.heartbeat(token)


def test_duplicate_tab_cannot_replace_owner(session):
    manager, _, voice = session
    token = manager.start()['token']
    with pytest.raises(RuntimeError): manager.start()
    with pytest.raises(PermissionError): manager.stop('wrong')
    assert manager.heartbeat(token)['active']
    voice.start.assert_called_once()


def test_bad_and_oversized_frames_are_rejected(session):
    manager, _, _ = session
    token = manager.start(microphone=False)['token']
    for frame in [b'', b'not an image', b'x' * (manager.MAX_BYTES + 1), frame_bytes((2100, 2000))]:
        with pytest.raises((ValueError, OSError)):
            manager.frame(token, frame)
    assert manager.status()['screen'] == 'waiting'


def test_disabled_devices_and_stale_frame(session):
    manager, clock, voice = session
    token = manager.start(microphone=False, screen=False, speaker=False)['token']
    voice.start.assert_not_called()
    with pytest.raises(ValueError): manager.frame(token, frame_bytes())
    manager.stop(token)
    token = manager.start(microphone=False)['token']
    manager.frame(token, frame_bytes())
    clock[0] += 16
    with pytest.raises(ValueError): manager.image(token)
    assert manager._frame is None


@pytest.fixture
def client(session, monkeypatch):
    monkeypatch.setattr(api, 'active_desktop', session[0])
    app = create_app(router_specs=(("apps.api.active_desktop_api", "router", "", ()),),
                     lifespan_context=noop_lifespan, include_dashboard=False)
    with TestClient(app, base_url='http://127.0.0.1', client=('127.0.0.1', 1234)) as client:
        yield client


def test_api_local_origin_and_explicit_activation(client):
    assert client.post('/api/active-desktop/start', json={}).status_code == 403
    headers = {'X-Jarvis-Client': 'dashboard', 'Origin': 'https://attacker.example'}
    assert client.post('/api/active-desktop/start', json={}, headers=headers).status_code == 403
    headers['Origin'] = 'http://127.0.0.1'
    response = client.post('/api/active-desktop/start', json={'microphone': False}, headers=headers)
    assert response.status_code == 200
    token = response.json()['token']
    headers['X-Jarvis-Session'] = token
    response = client.post('/api/active-desktop/frame', content=frame_bytes(), headers=headers)
    assert response.status_code == 200
    assert response.json()['screen'] == 'receiving'
    assert 'token' not in client.get('/api/active-desktop/status', headers=headers).json()
    assert client.post('/api/active-desktop/stop', headers=headers).status_code == 200
    assert client.post('/api/active-desktop/frame', content=frame_bytes(), headers=headers).status_code == 401


def test_api_describe_only_uses_local_endpoint(client, monkeypatch):
    headers = {'X-Jarvis-Client': 'dashboard'}
    token = client.post('/api/active-desktop/start', json={'microphone': False}, headers=headers).json()['token']
    headers['X-Jarvis-Session'] = token
    client.post('/api/active-desktop/frame', content=frame_bytes(), headers=headers)
    response = MagicMock()
    response.json.return_value = {'response': 'A blue screen.'}
    post = MagicMock(return_value=response)
    monkeypatch.setattr(api.requests, 'post', post)
    result = client.post('/api/active-desktop/describe', json={}, headers=headers)
    assert result.status_code == 200
    assert result.json()['description'] == 'A blue screen.'
    assert result.json()['verified'] is False
    assert post.call_args.args[0] == 'http://127.0.0.1:11434/api/generate'
    assert 'images' in post.call_args.kwargs['json']


def test_api_frame_validation_and_upload_limit(client, session):
    headers = {'X-Jarvis-Client': 'dashboard'}
    headers['X-Jarvis-Session'] = client.post(
        '/api/active-desktop/start', json={'microphone': False}, headers=headers,
    ).json()['token']
    for content, content_type, status in [
        (b'not an image', 'image/jpeg', 400),
        (frame_bytes(), 'text/plain', 415),
        (b'x' * (session[0].MAX_BYTES + 1), 'image/jpeg', 413),
        (frame_bytes(), 'image/png', 200),
    ]:
        result = client.post('/api/active-desktop/frame', content=content,
                             headers={**headers, 'Content-Type': content_type})
        assert result.status_code == status


def test_api_disabled_screen_rejects_frames(client):
    headers = {'X-Jarvis-Client': 'dashboard'}
    headers['X-Jarvis-Session'] = client.post('/api/active-desktop/start',
        json={'microphone': False, 'screen': False}, headers=headers).json()['token']
    result = client.post('/api/active-desktop/frame', content=frame_bytes(), headers=headers)
    assert result.status_code == 409
    assert 'disabled' in result.json()['detail']


def test_api_frame_requires_owner_before_validating_content(client):
    result = client.post('/api/active-desktop/frame', content=b'private frame',
                         headers={'X-Jarvis-Client': 'dashboard', 'Content-Type': 'text/plain'})
    assert result.status_code == 401


def test_stop_during_frame_decode_cannot_revive_capture(session, monkeypatch):
    manager, _, _ = session
    token = manager.start(microphone=False)['token']
    original_open = Image.open

    def open_and_revoke(*args, **kwargs):
        image = original_open(*args, **kwargs)
        manager.stop(token)
        return image

    monkeypatch.setattr(Image, 'open', open_and_revoke)
    with pytest.raises(PermissionError):
        manager.frame(token, frame_bytes())
    assert not manager.status()['active']
    assert manager._frame is None


def test_external_voice_daemon_does_not_start_second_owner(monkeypatch):
    import apps.voice.wake_word_engine as wake
    import apps.voice.service as service
    monkeypatch.setattr(wake, 'is_voice_service_daemon_running', lambda: True)
    start = MagicMock()
    monkeypatch.setattr(service.voice_service, 'start', start)
    lease = VoiceLease()
    assert lease.start()['state'] == 'external_owner'
    lease.stop()
    start.assert_not_called()


def test_voice_lease_preserves_running_owner(monkeypatch):
    import apps.voice.wake_word_engine as wake
    import apps.voice.service as service
    monkeypatch.setattr(wake, 'is_voice_service_daemon_running', lambda: False)
    monkeypatch.setattr(wake.wake_word_engine, '_is_running', True)
    voice = MagicMock()
    voice.is_muted.return_value = True
    voice.get_state.return_value = {'listening': True, 'microphone_available': True}
    monkeypatch.setattr(service, 'voice_service', voice)
    lease = VoiceLease()
    assert lease.start()['state'] == 'listening'
    lease.stop()
    voice.start.assert_not_called()
    voice.stop.assert_not_called()
    voice.unmute.assert_called_once()
    voice.mute.assert_called_once()


def test_push_to_talk_cannot_compete_with_voice_daemon(monkeypatch):
    import apps.voice.wake_word_engine as wake
    import apps.voice.service as service
    monkeypatch.setattr(wake, 'is_voice_service_daemon_running', lambda: True)
    monkeypatch.setattr(service.voice_service, '_muted', False)
    record = MagicMock()
    monkeypatch.setattr(service.voice_service.stt, 'record_audio', record)
    result = service.voice_service.listen_once()
    assert result['status'] == 'error'
    assert 'second capture' in result['message']
    record.assert_not_called()


def test_voice_start_api_preserves_daemon_owner(monkeypatch):
    import apps.voice.wake_word_engine as wake
    from apps.api.voice_api import start_voice_listening, voice_service
    monkeypatch.setattr(wake, 'is_voice_service_daemon_running', lambda: True)
    start = MagicMock()
    monkeypatch.setattr(voice_service, 'start', start)
    assert start_voice_listening()['status'] == 'existing_owner'
    start.assert_not_called()


def test_daemon_lookup_uses_user_bus_even_in_system_service(monkeypatch):
    import apps.voice.wake_word_engine as wake
    run = MagicMock(return_value=MagicMock(stdout='active\n', returncode=0))
    monkeypatch.setattr(wake.subprocess, 'run', run)
    monkeypatch.setattr(wake.os, 'getuid', lambda: 1234)
    assert wake.is_voice_service_daemon_running() is True
    assert run.call_args.kwargs['env']['XDG_RUNTIME_DIR'] == '/run/user/1234'
    assert run.call_args.kwargs['env']['DBUS_SESSION_BUS_ADDRESS'] == 'unix:path=/run/user/1234/bus'


def test_daemon_lookup_failure_does_not_authorize_another_capture(monkeypatch):
    import apps.voice.wake_word_engine as wake
    monkeypatch.setattr(wake.subprocess, 'run', MagicMock(return_value=MagicMock(stdout='', returncode=1)))
    with pytest.raises(RuntimeError, match='microphone owner'):
        wake.is_voice_service_daemon_running()


def test_ocr_uses_memory_only_and_treats_output_as_untrusted(client, monkeypatch):
    headers = {'X-Jarvis-Client': 'dashboard'}
    headers['X-Jarvis-Session'] = client.post('/api/active-desktop/start', json={'microphone': False}, headers=headers).json()['token']
    client.post('/api/active-desktop/frame', content=frame_bytes(), headers=headers)
    monkeypatch.setattr(api.shutil, 'which', lambda name: '/usr/bin/tesseract')
    run = MagicMock(return_value=MagicMock(returncode=0, stdout=b'Terminal error: missing module'))
    monkeypatch.setattr(api.subprocess, 'run', run)
    result = client.post('/api/active-desktop/read-text', headers=headers)
    assert result.status_code == 200
    assert result.json()['text'] == 'Terminal error: missing module'
    assert result.json()['verified'] is False
    assert run.call_args.args[0][1:3] == ['stdin', 'stdout']
    assert isinstance(run.call_args.kwargs['input'], bytes)


def test_ocr_missing_dependency_is_explicit(client, monkeypatch):
    headers = {'X-Jarvis-Client': 'dashboard'}
    headers['X-Jarvis-Session'] = client.post('/api/active-desktop/start', json={'microphone': False}, headers=headers).json()['token']
    client.post('/api/active-desktop/frame', content=frame_bytes(), headers=headers)
    monkeypatch.setattr(api.shutil, 'which', lambda name: None)
    result = client.post('/api/active-desktop/read-text', headers=headers)
    assert result.status_code == 503
    assert 'tesseract-ocr' in result.json()['detail']
