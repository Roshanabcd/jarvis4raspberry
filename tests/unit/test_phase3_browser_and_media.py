"""
Automated Unit and Integration Test Suite for JARVIS OS — Phase 3
Tests:
- Browser Agent & Search Manager (organic search, session memory, numbered navigation)
- YouTube Controller (real metadata extraction, player controls, state tracking)
- Audio Stream Manager (PipeWire per-stream volume, ducking, restoration, master sink protection)
- Wake Word Engine (12-state machine, acoustic patterns, 3s silence countdown, follow-up window)
- Theme Customization Manager (natural language commands, CSS variable persistence)
- Fast-Path Intent Classification for all Phase 3 commands
- Compound Multi-Task Orchestration
"""
import pytest
import re
from typing import Dict, Any

from tools.browser.search_manager import SearchManager, SearchSession, SearchRecord
from tools.browser.youtube_controller import YouTubeController, YouTubeSession, YouTubeVideo
from tools.media.audio_stream_manager import AudioStreamManager
from tools.desktop.theme_manager import ThemeManager
from apps.voice.wake_word_engine import WakeWordEngine, WakeState
from ai.local_engine import LocalIntelligenceEngine
from ai.agents.task_orchestrator import CompoundTaskOrchestrator


class TestSearchManager:
    """Tests for Phase 3C & 3D Search & Navigation."""

    def test_search_session_numbered_lookup(self):
        session = SearchSession(query="Raspberry Pi robotics")
        r1 = SearchRecord(1, "Best Robot Kits", "raspberrytips.com", "https://raspberrytips.com/robots")
        r2 = SearchRecord(2, "Official Projects", "raspberrypi.com", "https://raspberrypi.com/projects")
        r3 = SearchRecord(3, "Magazine Article", "magazine.raspberrypi.com", "https://magazine.raspberrypi.com/article")
        session.add_result(r1)
        session.add_result(r2)
        session.add_result(r3)

        # Test 1-based and 0-based lookup
        assert session.get_by_index(1).title == "Best Robot Kits"
        assert session.get_by_index(2).title == "Official Projects"
        assert session.get_by_index(3).title == "Magazine Article"
        assert session.get_by_index(0).title == "Best Robot Kits"
        assert session.get_by_index(99) is None

    def test_search_web_organic_results(self):
        sm = SearchManager()
        res = sm.search_web("Raspberry Pi 5", max_results=3)
        assert res["status"] == "ok"
        assert res["count"] > 0
        assert len(res["results"]) <= 3
        top = res["results"][0]
        assert top["rank"] == 1
        assert top["title"]
        assert top["domain"]
        assert top["url"].startswith("http")

        # Session must be stored
        active = sm.get_active_session()
        assert active is not None
        assert active["query"] == "Raspberry Pi 5"


class TestYouTubeController:
    """Tests for Phase 3E YouTube Automation."""

    def test_youtube_search_metadata_extraction(self):
        yt = YouTubeController()
        res = yt.search("Hindi songs", max_results=2)
        assert res["status"] == "ok"
        assert len(res["videos"]) == 2
        v1 = res["videos"][0]
        assert v1["rank"] == 1
        assert v1["video_id"]
        assert v1["title"]
        assert v1["url"].startswith("https://www.youtube.com/watch?v=")
        # Verify elimination of static "Me at the zoo" substitution
        assert "me at the zoo" not in v1["title"].lower()

    def test_youtube_session_resolution(self):
        yt = YouTubeController()
        session = YouTubeSession("test song")
        v1 = YouTubeVideo(1, "abc12345", "Song One", "Channel A", "https://www.youtube.com/watch?v=abc12345")
        v2 = YouTubeVideo(2, "xyz67890", "Song Two", "Channel B", "https://www.youtube.com/watch?v=xyz67890")
        session.add_video(v1)
        session.add_video(v2)
        yt._current_session = session

        # Resolve index 1 and 2
        assert yt._current_session.get_by_index(1).video_id == "abc12345"
        assert yt._current_session.get_by_index(2).video_id == "xyz67890"

    def test_player_state_tracking(self):
        yt = YouTubeController()
        st = yt.get_player_state()
        assert "is_playing" in st
        assert "is_paused" in st
        assert "volume_pct" in st


class TestAudioStreamManager:
    """Tests for Phase 3F & 3G Stream Separation & Music Preservation."""

    def test_active_stream_listing(self):
        asm = AudioStreamManager()
        streams = asm.list_active_streams()
        assert isinstance(streams, list)
        for s in streams:
            assert "stream_id" in s
            assert "name" in s
            assert "direction" in s
            assert "volume" in s

    def test_master_sink_volume(self):
        asm = AudioStreamManager()
        master = asm.get_master_sink_volume()
        assert "volume" in master
        assert "volume_pct" in master
        assert 0 <= master["volume_pct"] <= 150

    def test_stream_ducking_and_restoration(self):
        asm = AudioStreamManager()
        # Mock saved stream levels
        asm._ducked_streams[999] = 1.0
        restored = asm.restore_active_streams()
        # Verify dictionary cleared after restore
        assert len(asm._ducked_streams) == 0


class TestWakeWordEngine:
    """Tests for Phase 3H & 3I 12-State Voice Engine."""

    def test_twelve_states_defined(self):
        states = [s.value for s in WakeState]
        assert len(states) == 12
        expected = [
            "DISABLED", "STANDBY_LISTENING", "WAKE_DETECTED", "LISTENING_SPEECH",
            "STREAMING_TRANSCRIPTION", "SILENCE_COUNTDOWN", "COMMAND_SUBMITTED",
            "PROCESSING_AGENT", "SPEAKING_RESPONSE", "FOLLOW_UP_STANDBY", "MUTED", "ERROR"
        ]
        assert set(states) == set(expected)

    def test_wake_phrase_matching(self):
        engine = WakeWordEngine()
        assert engine._matches_wake_phrase("wake up jarvis") is True
        assert engine._matches_wake_phrase("wake up, jarvis please") is True
        assert engine._matches_wake_phrase("hey jarvis what time is it") is True
        assert engine._matches_wake_phrase("jarvis tell me the weather") is True
        assert engine._matches_wake_phrase("play a song") is False
        assert engine._matches_wake_phrase("open chrome") is False

    def test_state_transitions(self):
        engine = WakeWordEngine()
        assert engine.state == WakeState.DISABLED
        engine.set_state(WakeState.STANDBY_LISTENING)
        assert engine.state == WakeState.STANDBY_LISTENING
        engine.set_state(WakeState.WAKE_DETECTED)
        assert engine.state == WakeState.WAKE_DETECTED
        engine.set_state(WakeState.FOLLOW_UP_STANDBY)
        assert engine.state == WakeState.FOLLOW_UP_STANDBY
        engine.set_state(WakeState.DISABLED)


class TestThemeManager:
    """Tests for Phase 3L Theme Customization."""

    def test_natural_language_presets(self, tmp_path):
        cfg_file = str(tmp_path / "theme_test.json")
        tm = ThemeManager(config_path=cfg_file)

        # Set black background
        res_bg = tm.process_natural_language("Change background to black")
        assert res_bg["status"] == "ok"
        assert tm.get_theme()["bg_primary"] == "#000000"

        # Set green accent
        res_color = tm.process_natural_language("Make accent green")
        assert res_color["status"] == "ok"
        assert tm.get_theme()["color_accent"] == "#00ff88"

        # Reset theme
        res_reset = tm.process_natural_language("Reset theme")
        assert res_reset["status"] == "ok"
        assert tm.get_theme()["color_accent"] == "#00f3ff"


class TestIntentClassification:
    """Tests for Phase 3 Intent Classifiers in LocalIntelligenceEngine."""

    def test_phase3_intent_routes(self):
        engine = LocalIntelligenceEngine()

        routes = [
            ("Search Google for Raspberry Pi robotics", "google_search"),
            ("Open the first website", "browser_numbered_nav"),
            ("Open the second website", "browser_numbered_nav"),
            ("Open the third result in a new tab", "browser_numbered_nav"),
            ("Go back and open the second website", "browser_numbered_nav"),
            ("Go back", "browser_history_nav"),
            ("Search YouTube for a Hindi song", "youtube_search"),
            ("Play the first video", "youtube_play_index"),
            ("Play the second result instead", "youtube_play_index"),
            ("Pause the video", "youtube_pause"),
            ("Resume the video", "youtube_resume"),
            ("Switch the video to full screen", "youtube_fullscreen"),
            ("Mute the video", "youtube_mute"),
            ("Increase the video volume to 60 percent", "youtube_volume"),
            ("Change background to black", "theme_control"),
            ("Make accent cyan", "theme_control"),
            ("Set FreeTube volume to 80%", "stream_volume_control"),
            ("Set system volume to 60%", "master_volume_control"),
        ]

        for query, expected_intent in routes:
            intent, _ = engine.classify_intent(query)
            assert intent == expected_intent, f"Query '{query}' classified as '{intent}' instead of '{expected_intent}'"


class TestCompoundTaskOrchestration:
    """Tests for Phase 3N Multi-Task Orchestration."""

    def test_compound_detection_and_splitting(self):
        query = "Open YouTube, search for Hindi songs, play the first video, set its volume to 50 percent, and tell me the title"
        assert CompoundTaskOrchestrator.is_compound_request(query) is True
        subtasks = CompoundTaskOrchestrator.split_subtasks(query)
        assert len(subtasks) == 5
        assert subtasks[0] == "Open YouTube"
        assert subtasks[1] == "search for Hindi songs"
        assert subtasks[2] == "play the first video"
        assert subtasks[3] == "set its volume to 50 percent"
        assert subtasks[4] == "tell me the title"
