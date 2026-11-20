"""
FastAPI REST Integration Tests for JARVIS YouTube AI.
"""
import json
import tempfile
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest

from apps.core.app_factory import create_app, noop_lifespan


@pytest.fixture(scope="module")
def client():
    app = create_app(
        router_specs=[
            ("apps.api.youtube_api", "youtube_router", "/api", ("youtube",)),
            ("apps.api.apps_center_api", "apps_center_router", "/api", ("apps_center",)),
        ],
        lifespan_context=noop_lifespan,
        include_dashboard=False,
    )
    return TestClient(app)


def test_api_config(client):
    res = client.get("/api/youtube/config")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "supported_summary_types" in data
    assert "quick" in data["supported_summary_types"]


def test_api_validate_url(client):
    # Valid
    res = client.post("/api/youtube/validate-url", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert data["video_id"] == "dQw4w9WgXcQ"

    # SSRF Attack
    res_ssrf = client.post("/api/youtube/validate-url", json={"url": "http://169.254.169.254/latest/meta-data"})
    assert res_ssrf.status_code == 400
    assert "SSRF" in res_ssrf.json()["detail"]

    # Invalid
    res_inv = client.post("/api/youtube/validate-url", json={"url": "not_a_url"})
    assert res_inv.status_code == 200
    assert res_inv.json()["valid"] is False


def test_api_metadata_mocked(client):
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "title": "Quantum Physics for Beginners",
            "author_name": "MIT OpenCourseWare",
            "thumbnail_url": "https://i.ytimg.com/vi/qp123456789/hqdefault.jpg",
        }
        mock_get.return_value = mock_resp

        res = client.post("/api/youtube/metadata", json={"video_id": "qp123456789"})
        assert res.status_code == 200
        data = res.json()
        assert data["video_id"] == "qp123456789"
        assert "Quantum Physics" in data["title"]


def test_api_transcript_flow_and_summarize(client):
    video_id = "testvid9999"
    srt_content = """1
00:00:01,000 --> 00:00:04,000
[Prof Smith]: Welcome to introduction to computer systems.

2
00:00:05,000 --> 00:00:09,000
Today we study memory hierarchy and caches.
"""
    # 1. Upload transcript
    up_res = client.post(
        "/api/youtube/transcripts/upload",
        json={"video_id": video_id, "content": srt_content, "filename": "lecture.srt"},
    )
    assert up_res.status_code == 200
    up_data = up_res.json()
    assert up_data["status"] == "SUCCESS"
    assert up_data["segment_count"] == 2

    # 2. Get transcript
    get_res = client.get(f"/api/youtube/transcripts/{video_id}")
    assert get_res.status_code == 200
    t_data = get_res.json()
    assert t_data["status"] == "AVAILABLE"
    assert len(t_data["segments"]) == 2

    # Mock chat_completion for fast deterministic response
    with patch("apps.apps_center.ai_service.SharedAIService.chat_completion") as mock_chat:
        mock_chat.return_value = {
            "success": True,
            "text": "Based on the transcript, today we study memory hierarchy and caches.",
            "provider": "mock_test",
        }

        # 3. Summarize
        sum_res = client.post(
            "/api/youtube/summarize",
            json={"video_id": video_id, "summary_type": "quick"},
        )
        assert sum_res.status_code == 200
        sum_data = sum_res.json()
        assert sum_data["summary_type"] == "quick"
        assert len(sum_data["chapters"]) >= 1

        # 4. Ask Question
        ask_res = client.post(
            "/api/youtube/ask",
            json={"video_id": video_id, "question": "What do we study today?"},
        )
        assert ask_res.status_code == 200
        ans_data = ask_res.json()
        assert ans_data["grounded"] is True


def test_api_notes_crud_and_export(client):
    # 1. Create note
    create_res = client.post(
        "/api/youtube/notes",
        json={
            "video_id": "vid_api_test",
            "video_title": "API Test Note Video",
            "channel": "Test Channel",
            "summary_type": "detailed",
            "content": "This is note content.",
            "chapters": [{"title": "Ch1", "start_formatted": "00:00"}],
            "key_points": ["Point 1", "Point 2"],
        },
    )
    assert create_res.status_code == 200
    note_data = create_res.json()
    note_id = note_data["note_id"]

    # 2. List notes
    list_res = client.get("/api/youtube/notes")
    assert list_res.status_code == 200
    notes = list_res.json()
    assert any(n["note_id"] == note_id for n in notes)

    # 3. Export note
    exp_res = client.get(f"/api/youtube/notes/{note_id}/export?format=markdown")
    assert exp_res.status_code == 200
    assert "# API Test Note Video" in exp_res.text

    # 4. Delete note
    del_res = client.delete(f"/api/youtube/notes/{note_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "SUCCESS"


def test_api_history_endpoints(client):
    hist_res = client.get("/api/youtube/history")
    assert hist_res.status_code == 200
    assert isinstance(hist_res.json(), list)

    clear_res = client.delete("/api/youtube/history")
    assert clear_res.status_code == 200
    assert clear_res.json()["status"] == "SUCCESS"
