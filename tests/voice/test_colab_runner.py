"""
Unit tests for Google Colab OmniVoice AutoRunner subsystem and API endpoints.
"""

import os
import pytest
from apps.voice.colab_runner import ColabAutoRunner, get_colab_runner, GRADIO_URL_PATTERN


def test_colab_runner_singleton():
    runner1 = ColabAutoRunner()
    runner2 = get_colab_runner()
    assert runner1 is runner2
    assert runner1.session_name == "testColab"
    assert "Super_Eleven_Lab_Lite_2_1.ipynb" in runner1.notebook_path


def test_colab_runner_status_and_voice_binding():
    runner = get_colab_runner()
    st = runner.status()
    assert "state" in st
    assert "is_running" in st
    assert "session_name" in st
    assert "notebook_path" in st
    assert "voice_sample_path" in st
    assert st["voice_sample_exists"] is True
    assert os.path.exists(st["voice_sample_path"])


def test_gradio_url_regex_extraction():
    sample_colab_line = "* Running on public URL: https://eb0f339f7e0be198a9.gradio.live"
    match = GRADIO_URL_PATTERN.search(sample_colab_line)
    assert match is not None
    assert match.group(0) == "https://eb0f339f7e0be198a9.gradio.live"

    sample_colab_line_2 = "🔗 Public Gradio URL: https://a1b2c3d4-test.gradio.live/"
    match2 = GRADIO_URL_PATTERN.search(sample_colab_line_2)
    assert match2 is not None
    assert "gradio.live" in match2.group(0)


def test_on_url_discovered_mock(monkeypatch):
    runner = get_colab_runner()
    test_url = "https://mock-test-12345.gradio.live"
    
    registered_urls = []
    def mock_register_url(gradio_url, **kwargs):
        registered_urls.append(gradio_url)
        return {"status": "ok", "url": gradio_url}

    from apps.voice.colab_registration import colab_manager
    monkeypatch.setattr(colab_manager, "register_url", mock_register_url)

    runner._on_url_discovered(test_url)
    assert test_url in registered_urls


def test_colab_runner_api_endpoints():
    from fastapi.testclient import TestClient
    from apps.core.main import app

    client = TestClient(app)
    resp = client.get("/api/voice/colab/runner")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_name"] == "testColab"
    assert data["voice_sample_exists"] is True
