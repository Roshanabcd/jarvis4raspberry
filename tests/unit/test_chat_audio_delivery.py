from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from apps.core.app_factory import create_app, noop_lifespan


@pytest.fixture
def client(monkeypatch):
    import ai.brain
    import apps.voice.speech_manager
    brain = MagicMock()
    brain.chat.return_value = {'response': 'Hello'}
    brain.stream_chat.return_value = iter([{'type': 'token', 'content': 'Hello'}, {'type': 'done'}])
    monkeypatch.setattr(ai.brain, 'get_brain', lambda: brain)
    synth = MagicMock(return_value={'status': 'error', 'error': 'No local speech engine'})
    monkeypatch.setattr(apps.voice.speech_manager.speech_manager, 'synthesize_and_stage', synth)
    app = create_app(router_specs=(("apps.api.chat_api", "chat_router", "/api", ()),),
                     lifespan_context=noop_lifespan, include_dashboard=False)
    with TestClient(app) as client:
        yield client, synth


def test_browser_audio_does_not_play_twice(client):
    browser, synth = client
    response = browser.post('/api/chat', json={'message': 'Hi', 'speak': True, 'audio_output': 'browser'})
    assert response.status_code == 200
    assert response.json()['audio_error'] == 'No local speech engine'
    synth.assert_called_once_with('Hello', play_system=False)


def test_sse_reports_audio_failure_without_fake_playable_asset(client):
    browser, _ = client
    response = browser.post('/api/chat/stream', json={'message': 'Hi', 'speak': True, 'audio_output': 'browser'})
    assert 'audio_error' in response.text
    assert 'No local speech engine' in response.text
    assert 'audio_url' not in response.text


def test_speech_off_does_not_invoke_synthesis(client):
    browser, synth = client
    assert browser.post('/api/chat', json={'message': 'Hi', 'speak': False}).status_code == 200
    synth.assert_not_called()


def test_missing_synthesis_backend_is_failure_without_speaking(tmp_path, monkeypatch):
    from apps.voice.gradio_tts import GradioVoiceCloner
    cloner = GradioVoiceCloner(cache_dir=str(tmp_path), cloning_enabled=False)
    cloner.cloud_tts_enabled = False
    monkeypatch.setattr('apps.voice.gradio_tts.shutil.which', lambda name: None)
    speak = MagicMock()
    monkeypatch.setattr(cloner.fallback_tts, 'speak_sync', speak)
    result = cloner.synthesize('Offline staging test')
    assert result.success is False
    assert result.audio_path is None
    assert 'espeak-ng' in result.error
    speak.assert_not_called()
