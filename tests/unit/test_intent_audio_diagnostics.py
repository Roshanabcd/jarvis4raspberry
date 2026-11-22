"""
Unit Tests for Intent Disambiguation, Audio Diagnostics, Truthful YouTube Status,
and Developer CLI Escalation Bridge.
"""
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from ai.local_engine import local_engine
from tools.developer.cli_bridge import developer_cli_bridge
from tools.browser.youtube_controller import (
    YouTubeController,
    YouTubeVideo,
    STATE_PLAYING_VERIFIED,
    STATE_PLAYBACK_BLOCKED,
    STATE_OPENED_PAUSED,
)


class TestIntentAudioDiagnostics(unittest.TestCase):
    """Test intent classification rules and audio troubleshooting routing."""

    def test_audio_diagnostics_disambiguation(self):
        """User audio troubleshooting queries must route to audio_diagnostics, NEVER camera_capture."""
        queries = [
            "can you able to see why sound is not listening that you played video right now",
            "why is sound not working",
            "why is audio not playing",
            "why can't i hear the video",
            "can't hear anything from the speaker",
            "no sound from youtube",
            "diagnose audio",
            "troubleshoot sound",
            "check pipewire audio",
        ]
        for q in queries:
            intent, _ = local_engine.classify_intent(q)
            self.assertEqual(
                intent,
                "audio_diagnostics",
                f"Query '{q}' should route to 'audio_diagnostics', but got '{intent}'",
            )

    def test_camera_intents_preserved(self):
        """Explicit visual capture and description intents must still route to camera correctly."""
        cam_capture_queries = [
            "Capture my photo",
            "take a photo",
            "take a picture",
            "take snapshot",
            "camera snapshot",
            "camera capture",
        ]
        for q in cam_capture_queries:
            intent, _ = local_engine.classify_intent(q)
            self.assertEqual(
                intent,
                "camera_capture",
                f"Query '{q}' should route to 'camera_capture', but got '{intent}'",
            )

        desc_intent, _ = local_engine.classify_intent("What do you see in the room?")
        self.assertEqual(desc_intent, "camera_describe")

    def test_developer_escalation_intent(self):
        """Developer escalation and diagnosis phrases must route to developer_escalation."""
        intent_esc, args_esc = local_engine.classify_intent("escalate to developer cli")
        self.assertEqual(intent_esc, "developer_escalation")
        self.assertEqual(args_esc.get("action"), "diagnose")

        intent_agy, args_agy = local_engine.classify_intent("diagnose with agy")
        self.assertEqual(intent_agy, "developer_escalation")
        self.assertEqual(args_agy.get("cli"), "agy")

        intent_fix, args_fix = local_engine.classify_intent("run developer fix")
        self.assertEqual(intent_fix, "developer_escalation")
        self.assertEqual(args_fix.get("action"), "propose_or_run_fix")

    def test_audio_diagnostics_response_structure(self):
        """Audio diagnostics handler returns structured markdown with sink, streams, and tips."""
        resp = local_engine.respond("why is sound not working")
        self.assertIn("response", resp)
        text = resp["response"]
        self.assertIn("Audio & Playback Diagnostics", text)
        self.assertIn("Master Sink", text)
        self.assertIn("Remediation Steps", text)
        self.assertIn("raw", resp)
        self.assertIn("master_volume", resp["raw"])

    def test_gated_developer_fix_requires_auth(self):
        """Attempting to run a developer fix via chat prompts for administrator authorization."""
        resp = local_engine.respond("run developer fix")
        self.assertIn("Gated Developer Action Required", resp["response"])
        self.assertIn("admin PIN", resp["response"])


class TestYouTubeTruthfulStatusAndMetadata(unittest.TestCase):
    """Test YouTube playback truthful status and channel metadata extraction."""

    def test_truthful_playback_status_formatting(self):
        """When state is PLAYBACK_BLOCKED, response must NOT say 'Now playing'."""
        with patch("tools.browser.youtube_controller.youtube_controller.select_and_play") as mock_play:
            mock_play.return_value = {
                "status": "ok",
                "state": STATE_PLAYBACK_BLOCKED,
                "rank": 1,
                "title": "Namami Shamishan Nirvan Roopam",
                "channel": "Mamta Thakur",
                "duration": "05:30",
                "url": "https://www.youtube.com/watch?v=kffacxfA7G4",
            }
            resp = local_engine.respond("play option 1")
            text = resp["response"]

            # Must NOT claim 'Now playing'
            self.assertNotIn("Now playing", text)
            # Must state 'Playback Blocked'
            self.assertIn("Playback Blocked", text)
            # Must include unlock tip
            self.assertIn("Tip: Click inside the YouTube Chrome window", text)

    def test_truthful_playback_status_verified(self):
        """When state is PLAYING_VERIFIED, response accurately states 'Now playing'."""
        with patch("tools.browser.youtube_controller.youtube_controller.select_and_play") as mock_play:
            mock_play.return_value = {
                "status": "ok",
                "state": STATE_PLAYING_VERIFIED,
                "rank": 1,
                "title": "Namami Shamishan Nirvan Roopam",
                "channel": "Mamta Thakur",
                "duration": "05:30",
                "url": "https://www.youtube.com/watch?v=kffacxfA7G4",
            }
            resp = local_engine.respond("play option 1")
            text = resp["response"]

            self.assertIn("Now playing", text)
            self.assertIn("Audio stream verified active", text)

    def test_channel_name_fallback_chain(self):
        """Metadata extraction uses fallback attributes and oEmbed lookup."""
        yt = YouTubeController()
        # Mock yt-dlp returning empty channel/uploader but valid id
        mock_output = '{"id": "test1234", "title": "Test Title", "uploader": null, "channel": null, "duration_string": "03:00"}'
        with patch("subprocess.run") as mock_sub:
            mock_sub.return_value = MagicMock(stdout=mock_output, returncode=0)
            with patch("urllib.request.urlopen") as mock_url:
                mock_resp = MagicMock()
                mock_resp.status = 200
                mock_resp.read.return_value = b'{"author_name": "Verified Channel Name"}'
                mock_url.return_value.__enter__.return_value = mock_resp

                videos = yt._extract_youtube_videos("test query", max_results=1)
                self.assertEqual(len(videos), 1)
                self.assertEqual(videos[0].channel, "Verified Channel Name")


class TestDeveloperCliBridge(unittest.TestCase):
    """Test Developer CLI Escalation Bridge detection, diagnosis, and gating."""

    def test_detect_clis(self):
        """Bridge accurately detects presence of installed developer CLIs."""
        res = developer_cli_bridge.detect_clis()
        self.assertIn("antigravity", res)
        self.assertIn("claude", res)
        # agy and claude are installed on this Pi
        self.assertTrue(res["has_developer_cli"])
        self.assertTrue(res["antigravity"]["installed"] or res["claude"]["installed"])

    def test_read_only_diagnosis(self):
        """diagnose_system() returns read-only Markdown report without errors."""
        diag = developer_cli_bridge.diagnose_system()
        self.assertIn("markdown_report", diag)
        report = diag["markdown_report"]
        self.assertIn("Developer CLI Auto-Inspection Report", report)
        self.assertIn("Service & Hardware Health", report)
        self.assertIn("jarvis-core.service", report)
        self.assertIn("Audio Master Sink", report)

    def test_gated_remediation_denies_without_pin(self):
        """Mutating action without valid PIN is denied."""
        res = developer_cli_bridge.execute_remediation(action="unmute_audio", pin="")
        self.assertEqual(res.get("status"), "error")
        self.assertEqual(res.get("code"), "AUTHENTICATION_FAILED")

        res_wrong = developer_cli_bridge.execute_remediation(action="unmute_audio", pin="00000000_invalid")
        self.assertEqual(res_wrong.get("status"), "error")
        self.assertEqual(res_wrong.get("code"), "AUTHENTICATION_FAILED")

    def test_gated_remediation_permits_with_verified_pin(self):
        """Mutating action with valid PIN authorization executes cleanly."""
        with patch.object(developer_cli_bridge, "verify_authorization", return_value=(True, "PIN verified")):
            with patch("subprocess.run") as mock_sub:
                mock_sub.return_value = MagicMock(returncode=0)
                res = developer_cli_bridge.execute_remediation(action="unmute_audio", pin="mock_valid_pin")
                self.assertEqual(res.get("status"), "ok")
                self.assertEqual(res.get("action"), "unmute_audio")


if __name__ == "__main__":
    unittest.main()
