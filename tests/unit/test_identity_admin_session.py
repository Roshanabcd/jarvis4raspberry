"""Admin setup/login tests use a private temporary identity store, never real accounts."""
import threading
from unittest.mock import MagicMock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from tools.identity import user_manager as identity_store
from tools.identity.user_manager import UserManager
from apps.api import identity_api
from apps.voice.session_manager import voice_session_mgr
from tools.identity.permission_manager import permission_manager


@pytest.fixture
def identity_client(tmp_path, monkeypatch):
    manager = object.__new__(UserManager)
    manager._lock = threading.RLock()
    manager._users = {}
    manager._failed_pin_attempts = 0
    manager._lockout_until = 0.0
    manager._max_pin_attempts = 5
    manager._lockout_duration_s = 60.0
    monkeypatch.setattr(identity_store, 'USERS_FILE', tmp_path / 'users.json')
    monkeypatch.setattr(identity_api, 'user_manager', manager)
    monkeypatch.setattr('apps.voice.session_manager.user_manager', manager)
    monkeypatch.setattr(permission_manager, 'user_mgr', manager)
    prior = voice_session_mgr._current_session
    voice_session_mgr.invalidate_session()
    camera = MagicMock(side_effect=AssertionError('PIN-only flow must not capture images'))
    monkeypatch.setattr(identity_api, 'CameraManager', camera)
    app = FastAPI()
    app.include_router(identity_api.identity_router, prefix='/api')
    with TestClient(app, base_url='http://127.0.0.1', client=('127.0.0.1', 50000)) as client:
        client.headers['X-Jarvis-Client'] = 'dashboard'
        yield client, manager, camera
    voice_session_mgr._current_session = prior


def enroll(client):
    return client.post('/api/identity/enroll_admin', json={
        'display_name': 'Test Administrator', 'pin': 'test-pin-123', 'confirmed': True, 'pin_only': True})


def test_pin_only_setup_sign_in_logout_and_same_role_everywhere(identity_client):
    client, manager, camera = identity_client
    assert client.get('/api/identity/status').json()['authorization_role'] == 'GUEST'
    result = enroll(client)
    assert result.status_code == 200
    assert result.json()['signed_in'] is True
    assert result.json()['authorization_role'] == 'ADMIN'
    assert manager.get_admin_user()['has_face_enrolled'] is False
    assert permission_manager.get_active_user()['role'] == 'ADMIN'
    assert voice_session_mgr.get_active_session().is_authenticated
    assert client.post('/api/identity/logout').status_code == 200
    assert permission_manager.get_active_user()['role'] == 'GUEST'
    result = client.post('/api/identity/verify_pin', json={'pin': 'test-pin-123'})
    assert result.status_code == 200
    assert result.json()['authorization_role'] == 'ADMIN'
    assert client.get('/api/identity/status').json()['active_user']['role'] == 'ADMIN'
    camera.assert_not_called()


def test_wrong_pin_never_elevates_and_lockout_remains(identity_client):
    client, _, _ = identity_client
    enroll(client)
    client.post('/api/identity/logout')
    for _ in range(5):
        assert client.post('/api/identity/verify_pin', json={'pin': 'wrong'}).status_code == 401
    assert client.post('/api/identity/verify_pin', json={'pin': 'test-pin-123'}).status_code == 401
    assert permission_manager.get_active_user()['role'] == 'GUEST'
    assert client.get('/api/identity/status').json()['is_pin_locked'] is True


def test_admin_expiry_is_consistent(identity_client):
    client, _, _ = identity_client
    enroll(client)
    voice_session_mgr._current_session.expires_at = 0
    status = client.get('/api/identity/status').json()
    assert status['authorization_role'] == status['active_user']['role'] == 'GUEST'


def test_voice_refresh_preserves_valid_pin_session_without_camera(identity_client, monkeypatch):
    client, _, _ = identity_client
    enroll(client)
    capture = MagicMock(side_effect=AssertionError('must not capture'))
    monkeypatch.setattr('apps.voice.session_manager.camera_manager.capture_photo', capture)
    before = voice_session_mgr.get_active_session().expires_at
    result = voice_session_mgr.identify_speaker_from_camera()
    assert result['source'] == 'admin_pin'
    assert result['authorization_role'] == 'ADMIN'
    assert voice_session_mgr.get_active_session().expires_at == before
    capture.assert_not_called()


def test_setup_requires_confirmation_and_cannot_replace_admin(identity_client):
    client, _, camera = identity_client
    r = client.post('/api/identity/enroll_admin', json={'display_name': 'Test', 'pin': '1234', 'pin_only': True})
    assert r.status_code == 400
    assert enroll(client).status_code == 200
    assert enroll(client).status_code == 409
    camera.assert_not_called()


def test_cross_origin_sign_in_is_rejected(identity_client):
    client, _, _ = identity_client
    r = client.post('/api/identity/verify_pin', json={'pin': '1234'}, headers={'Origin': 'https://untrusted.example'})
    assert r.status_code == 403


def test_recognized_admin_requires_pin(identity_client):
    client, _, _ = identity_client
    enroll(client)
    permission_manager.set_active_user({'user_id': 'recognized', 'display_name': 'Recognized', 'role': 'ADMIN'})
    assert permission_manager.get_active_user()['role'] == 'USER'
    assert voice_session_mgr.get_active_session().authorization_role() == 'USER'


def test_failed_persistence_does_not_create_phantom_admin(identity_client, monkeypatch):
    client, manager, _ = identity_client
    def fail():
        raise PermissionError('test storage denied')
    monkeypatch.setattr(manager, '_save_users', fail)
    assert enroll(client).status_code == 400
    assert manager.is_admin_enrolled() is False
    assert permission_manager.get_active_user()['role'] == 'GUEST'


def test_identity_store_is_private_and_pin_is_not_plaintext(identity_client):
    client, _, _ = identity_client
    assert enroll(client).status_code == 200
    path = identity_store.USERS_FILE
    assert path.stat().st_mode & 0o777 == 0o600
    assert 'test-pin-123' not in path.read_text()
