"""
Comprehensive Unit and Integration Test Suite for YouTube Selection Repair in JARVIS OS.

Verifies:
1. YouTube search extraction with organic metadata, thumbnails, duration, and AWAITING_USER_SELECTION state.
2. User-controlled video selection by index (1-based) or title match with Chrome playback verification.
3. Natural-language query parsing ("Open a horror video in YouTube" -> "Play the first horror movie in YouTube").
4. Prevention of generic media_player hijacking (never playing "Ramayana Movie Review" or background audio).
5. Open without playing (autoplay=False) and player controls (pause, resume, fullscreen, mute, volume).
6. Honest error handling for out-of-bounds indices and missing active sessions.
7. Cancellation of active sessions and fetching additional results.
8. REST API endpoints for search, session, select, cancel, more, and status.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from tools.browser.youtube_controller import (
    YouTubeController,
    YouTubeSession,
    YouTubeVideo,
    STATE_AWAITING_USER_SELECTION,
    STATE_SELECTION_CONFIRMED,
    STATE_PLAYING_VERIFIED,
    STATE_OPENED_PAUSED,
    STATE_VIDEO_NOT_AVAILABLE,
    STATE_CANCELLED,
    STATE_FAILED,
)
from ai.local_engine import LocalIntelligenceEngine
from tools.media.media_player import MediaPlayer
from apps.core.main import app


@pytest.fixture
def clean_controller():
    """Provides a fresh YouTubeController instance with mock browser agent."""
    controller = YouTubeController()
    return controller


@pytest.fixture
def populated_controller(clean_controller):
    """Provides a controller pre-populated with 5 organic horror video search results."""
    session = YouTubeSession(query="horror movie")
    videos = [
        YouTubeVideo(1, "vid_001", "The Conjuring: Official Full Trailer", "Warner Bros", "https://www.youtube.com/watch?v=vid_001", "2:30", "https://i.ytimg.com/vi/vid_001/hqdefault.jpg"),
        YouTubeVideo(2, "vid_002", "Insidious - Scariest Scenes", "FilmClips", "https://www.youtube.com/watch?v=vid_002", "15:40", "https://i.ytimg.com/vi/vid_002/hqdefault.jpg"),
        YouTubeVideo(3, "vid_003", "Top 10 Horror Movies of 2025", "WatchMojo", "https://www.youtube.com/watch?v=vid_003", "12:10", "https://i.ytimg.com/vi/vid_003/hqdefault.jpg"),
        YouTubeVideo(4, "vid_004", "Hereditary Explained in Depth", "CinemaWins", "https://www.youtube.com/watch?v=vid_004", "18:05", "https://i.ytimg.com/vi/vid_004/hqdefault.jpg"),
        YouTubeVideo(5, "vid_005", "Classic Dracula 1931 Full Feature", "HorrorCentral", "https://www.youtube.com/watch?v=vid_005", "1:15:00", "https://i.ytimg.com/vi/vid_005/hqdefault.jpg"),
    ]
    for v in videos:
        session.add_video(v)
    session.state = STATE_AWAITING_USER_SELECTION
    clean_controller._current_session = session
    clean_controller._sessions[session.session_id] = session
    return clean_controller


class TestYouTubeControllerCore:
    """Core controller session lifecycle, selection, and error handling."""

    def test_search_creates_session_awaiting_user_selection(self, clean_controller):
        """Search must extract videos, create a session with state AWAITING_USER_SELECTION, and not auto-play."""
        mock_videos = [
            YouTubeVideo(1, "abc1", "Horror Short Film", "SpookyChannel", "https://www.youtube.com/watch?v=abc1", "10:00"),
            YouTubeVideo(2, "abc2", "Haunted House Documentary", "DocuZone", "https://www.youtube.com/watch?v=abc2", "45:00"),
        ]
        with patch.object(clean_controller, "_extract_youtube_videos", return_value=mock_videos):
            res = clean_controller.search("horror movie", max_results=2)

        assert res["status"] == "ok"
        assert res["state"] == STATE_AWAITING_USER_SELECTION
        assert res["count"] == 2
        assert len(res["videos"]) == 2
        assert "Which video would you like me to open?" in res["formatted_summary"]

        session = clean_controller.get_session()
        assert session is not None
        assert session["state"] == STATE_AWAITING_USER_SELECTION
        assert session["query"] == "horror movie"
        assert len(session["videos"]) == 2

    def test_select_option_2_opens_in_chrome_and_verifies(self, populated_controller):
        """Selecting option 2 opens exact URL in Google Chrome with verified playback."""
        with patch("tools.browser.browser_agent.browser_agent.open_url", return_value={"status": "ok", "pid": 12345}), \
             patch("tools.browser.browser_agent.browser_agent.find_browser_windows", return_value=[{"window_id": "0x123", "title": "Insidious"}]):
            res = populated_controller.select_and_play(index=2, browser="chrome")

        assert res["status"] == "ok"
        assert res["state"] == STATE_PLAYING_VERIFIED
        assert res["rank"] == 2
        assert res["video_id"] == "vid_002"
        assert res["title"] == "Insidious - Scariest Scenes"
        assert res["channel"] == "FilmClips"
        assert res["url"] == "https://www.youtube.com/watch?v=vid_002"
        assert res["autoplay"] is True
        assert res["verification"]["verified"] is True

    def test_out_of_bounds_selection_returns_honest_error(self, populated_controller):
        """Selecting an invalid index returns honest error without guessing or substituting."""
        res = populated_controller.select_and_play(index=10)
        assert res["status"] == "error"
        assert res["code"] == "INDEX_OUT_OF_BOUNDS"
        assert res["state"] == STATE_VIDEO_NOT_AVAILABLE
        assert "Video option 10 is out of bounds" in res["message"]
        assert "The current search only has 5 options" in res["message"]

    def test_selection_when_no_active_session_prompts_user(self, clean_controller):
        """Attempting to select when no search session exists asks user to search first."""
        res = clean_controller.select_and_play(index=1)
        assert res["status"] == "error"
        assert res["code"] == "NO_ACTIVE_SESSION"
        assert "No active YouTube search found. Please search for a topic first" in res["message"]

    def test_open_option_without_playing(self, populated_controller):
        """Open option with autoplay=False opens Chrome and pauses video."""
        with patch("tools.browser.browser_agent.browser_agent.open_url", return_value={"status": "ok", "pid": 12345}), \
             patch("tools.browser.browser_agent.browser_agent.send_shortcut", return_value={"status": "ok"}), \
             patch("tools.browser.browser_agent.browser_agent.find_browser_windows", return_value=[{"window_id": "0x123", "title": "The Conjuring"}]):
            res = populated_controller.open_without_playing(index=1, browser="chrome")

        assert res["status"] == "ok"
        assert res["state"] == STATE_OPENED_PAUSED
        assert res["autoplay"] is False
        assert res["rank"] == 1
        assert populated_controller._is_paused is True
        assert populated_controller._is_playing is False

    def test_cancel_active_selection(self, populated_controller):
        """Cancelling session marks state CANCELLED and blocks follow-up selections."""
        c_res = populated_controller.cancel_selection()
        assert c_res["status"] == "ok"
        assert c_res["state"] == STATE_CANCELLED
        assert "cancelled" in c_res["message"].lower()

        # Follow-up selection must now fail
        next_sel = populated_controller.select_and_play(index=1)
        assert next_sel["status"] == "error"
        assert next_sel["code"] == "NO_ACTIVE_SESSION"

    def test_get_more_results(self, populated_controller):
        """Getting more results appends new videos and maintains AWAITING_USER_SELECTION."""
        extra_videos = [
            YouTubeVideo(1, "vid_006", "The Ring Full Review", "SpookMaster", "https://www.youtube.com/watch?v=vid_006", "11:20"),
            YouTubeVideo(2, "vid_007", "Sinister Analysis", "HorrorVault", "https://www.youtube.com/watch?v=vid_007", "14:15"),
        ]
        with patch.object(populated_controller, "_extract_youtube_videos", return_value=populated_controller._current_session.videos + extra_videos):
            res = populated_controller.get_more_results(count=2)

        assert res["status"] == "ok"
        assert res["state"] == STATE_AWAITING_USER_SELECTION
        assert res["total_videos"] == 7
        assert res["added_count"] == 2
        assert populated_controller._current_session.videos[5].rank == 6
        assert populated_controller._current_session.videos[6].rank == 7

    def test_select_by_title_match(self, populated_controller):
        """Selecting by keywords from the title resolves to the correct video."""
        with patch("tools.browser.browser_agent.browser_agent.open_url", return_value={"status": "ok", "pid": 12345}), \
             patch("tools.browser.browser_agent.browser_agent.find_browser_windows", return_value=[{"window_id": "0x123", "title": "Hereditary"}]):
            res = populated_controller.select_and_play(title_query="Hereditary Explained", browser="chrome")

        assert res["status"] == "ok"
        assert res["rank"] == 4
        assert res["video_id"] == "vid_004"
        assert "Hereditary" in res["title"]

    def test_player_controls(self, populated_controller):
        """Player controls (pause, resume, fullscreen, mute, volume) work and update state."""
        with patch("tools.browser.browser_agent.browser_agent.send_shortcut", return_value={"status": "ok"}):
            p_res = populated_controller.pause()
            assert p_res["status"] == "ok"
            assert populated_controller._is_paused is True

            r_res = populated_controller.resume()
            assert r_res["status"] == "ok"
            assert populated_controller._is_playing is True

            f_res = populated_controller.toggle_fullscreen()
            assert f_res["status"] == "ok"
            assert populated_controller._is_fullscreen is True

            m_res = populated_controller.mute()
            assert m_res["status"] == "ok"

        with patch("tools.media.audio_stream_manager.audio_stream_manager.set_app_volume", return_value={"count": 1}):
            v_res = populated_controller.set_video_volume(75)
            assert v_res["status"] == "ok"
            assert populated_controller._player_volume_pct == 75

        st = populated_controller.get_player_state()
        assert st["volume_pct"] == 75
        assert st["is_fullscreen"] is True


class TestLocalEngineIntentAndNaturalLanguage:
    """Natural-language classification, conversational flow, and anti-hijacking."""

    def test_natural_language_intent_classification(self):
        engine = LocalIntelligenceEngine()

        # Searches
        assert engine.classify_intent("Open a horror video in YouTube")[0] == "youtube_search"
        assert engine.classify_intent("Search YouTube for a horror movie")[0] == "youtube_search"
        assert engine.classify_intent("Find a relaxing song on YouTube")[0] == "youtube_search"
        assert engine.classify_intent("YouTube search for robotics")[0] == "youtube_search"

        # Selections
        assert engine.classify_intent("Play option 1")[0] == "youtube_play_index"
        assert engine.classify_intent("Play option 2")[0] == "youtube_play_index"
        assert engine.classify_intent("Play the first horror movie in YouTube")[0] == "youtube_play_index"
        assert engine.classify_intent("Play the second result instead")[0] == "youtube_play_index"
        assert engine.classify_intent("Open option 3 without playing")[0] == "youtube_play_index"
        assert engine.classify_intent("Choose option 4")[0] == "youtube_play_index"

        # Cancellation & More
        assert engine.classify_intent("Cancel selection")[0] == "youtube_cancel_selection"
        assert engine.classify_intent("Cancel")[0] == "youtube_cancel_selection"
        assert engine.classify_intent("Show 3 more results")[0] == "youtube_more_results"
        assert engine.classify_intent("Show more results")[0] == "youtube_more_results"

    def test_media_player_does_not_hijack_youtube_selection(self):
        """Generic play_media must NOT catch YouTube selection commands."""
        engine = LocalIntelligenceEngine()
        intent, ctx = engine.classify_intent("Play the first horror movie in YouTube")
        assert intent == "youtube_play_index"
        assert intent != "play_media"

        intent2, ctx2 = engine.classify_intent("Play option 1")
        assert intent2 == "youtube_play_index"
        assert intent2 != "play_media"

    def test_complete_horror_search_and_selection_flow(self):
        """End-to-end conversation simulation:
        User: 'Open a horror video in YouTube' -> displayed 5 choices
        User: 'Play the first horror movie in YouTube' -> plays option 1 in Chrome
        """
        from tools.browser.youtube_controller import youtube_controller

        mock_videos = [
            YouTubeVideo(1, "h_001", "The Nun 2 Official Trailer", "Warner Bros", "https://www.youtube.com/watch?v=h_001", "2:15"),
            YouTubeVideo(2, "h_002", "Halloween 1978 Masterpiece", "ClassicFilms", "https://www.youtube.com/watch?v=h_002", "1:31:00"),
        ]

        engine = LocalIntelligenceEngine()

        with patch.object(youtube_controller, "_extract_youtube_videos", return_value=mock_videos):
            resp1 = engine.respond("Open a horror video in YouTube")

        assert "The Nun 2 Official Trailer" in resp1["response"]
        assert "Halloween 1978 Masterpiece" in resp1["response"]
        assert "Which video would you like me to open?" in resp1["response"]
        assert youtube_controller.get_session()["state"] == STATE_AWAITING_USER_SELECTION

        # User selects: "Play the first horror movie in YouTube"
        with patch("tools.browser.browser_agent.browser_agent.open_url", return_value={"status": "ok", "pid": 11111}), \
             patch("tools.browser.browser_agent.browser_agent.find_browser_windows", return_value=[{"window_id": "0xabc", "title": "The Nun 2"}]):
            resp2 = engine.respond("Play the first horror movie in YouTube")

        assert "Now playing option #1" in resp2["response"]
        assert "The Nun 2 Official Trailer" in resp2["response"]
        assert "Warner Bros" in resp2["response"]
        assert "Ramayana" not in resp2["response"]
        assert "Yogi Bolta Hai" not in resp2["response"]
        assert youtube_controller.get_session()["state"] == STATE_PLAYING_VERIFIED


class TestMediaPlayerSafety:
    """Verifies MediaPlayer defensive checks against online audio hijacking."""

    def test_media_player_redirects_youtube_selection(self):
        mp = MediaPlayer()
        with patch("tools.browser.youtube_controller.youtube_controller.select_and_play", return_value={"status": "ok", "title": "Horror Video", "message": "Now playing in Chrome."}) as mock_sel:
            res = mp.play("Play the first horror movie in YouTube")
            assert mock_sel.called
            assert res["status"] == "playing"
            assert res["source"] == "youtube_chrome"


class TestYouTubeRestApi:
    """REST API endpoints verification."""

    def test_api_search_session_select_cancel(self):
        client = TestClient(app)

        mock_videos = [
            YouTubeVideo(1, "test_1", "Test Horror 1", "HorrorChannel", "https://www.youtube.com/watch?v=test_1", "3:00"),
            YouTubeVideo(2, "test_2", "Test Horror 2", "HorrorChannel", "https://www.youtube.com/watch?v=test_2", "4:00"),
        ]

        from tools.browser.youtube_controller import youtube_controller
        with patch.object(youtube_controller, "_extract_youtube_videos", return_value=mock_videos):
            # 1. Search
            r_search = client.post("/api/browser/youtube/search", json={"query": "horror movie", "max_results": 2})
            assert r_search.status_code == 200
            d_search = r_search.json()
            assert d_search["status"] == "ok"
            assert d_search["state"] == STATE_AWAITING_USER_SELECTION
            assert d_search["count"] == 2

            # 2. Get session
            r_sess = client.get("/api/browser/youtube/session")
            assert r_sess.status_code == 200
            d_sess = r_sess.json()
            assert d_sess["has_active_session"] is True
            assert d_sess["session"]["state"] == STATE_AWAITING_USER_SELECTION

            # 3. Select option 1
            with patch("tools.browser.browser_agent.browser_agent.open_url", return_value={"status": "ok", "pid": 9999}), \
                 patch("tools.browser.browser_agent.browser_agent.find_browser_windows", return_value=[{"window_id": "0x1", "title": "Test Horror 1"}]):
                r_sel = client.post("/api/browser/youtube/select", json={"index": 1, "browser": "chrome"})
                assert r_sel.status_code == 200
                d_sel = r_sel.json()
                assert d_sel["status"] == "ok"
                assert d_sel["state"] == STATE_PLAYING_VERIFIED
                assert d_sel["rank"] == 1
                assert d_sel["title"] == "Test Horror 1"

            # 4. Cancel
            r_cancel = client.post("/api/browser/youtube/cancel")
            assert r_cancel.status_code == 200
            assert r_cancel.json()["state"] == STATE_CANCELLED
