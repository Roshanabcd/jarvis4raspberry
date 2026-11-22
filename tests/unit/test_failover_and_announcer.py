"""
Unit tests for Automatic Quota Failover, Soft-Failure Detection, and Spoken Announcements.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from apps.voice.task_announcer import (
    clean_spoken_text,
    make_completion_summary,
    announce_task_completion,
)
from tools.developer.cli_bridge import (
    DeveloperCliBridge,
    detect_requested_output_file,
    is_image_task,
    is_soft_failure,
)


class TestSoftFailureAndDetection:
    def test_soft_failure_exit_code_zero_with_quota_markers(self):
        failed, reason = is_soft_failure("Error 429: RESOURCE_EXHAUSTED. Quota exceeded for model.", 0)
        assert failed is True
        assert "429" in reason or "quota" in reason.lower()

    def test_soft_failure_exit_code_zero_clean_output(self):
        failed, reason = is_soft_failure("Task completed cleanly and all files updated.", 0)
        assert failed is False
        assert reason == ""

    def test_soft_failure_non_zero_exit_code(self):
        failed, reason = is_soft_failure("General error", 1)
        assert failed is True
        assert "Exit code 1" in reason

    def test_target_file_missing_on_disk(self):
        with tempfile.TemporaryDirectory() as td:
            missing_path = os.path.join(td, "nonexistent.jpg")
            failed, reason = is_soft_failure("Success", 0, target_file=missing_path)
            assert failed is True
            assert "was not created on disk" in reason

    def test_target_file_zero_bytes_on_disk(self):
        with tempfile.NamedTemporaryFile(suffix=".png") as tf:
            # tf is 0 bytes
            failed, reason = is_soft_failure("Success", 0, target_file=tf.name)
            assert failed is True
            assert "empty (0 bytes)" in reason

    def test_target_file_valid_on_disk(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
            tf.write(b"PNGDATA123")
            tf.flush()
            try:
                failed, reason = is_soft_failure("Success", 0, target_file=tf.name)
                assert failed is False
                assert reason == ""
            finally:
                os.unlink(tf.name)


class TestPromptParsing:
    def test_detect_requested_output_file(self):
        p1 = "generate an image of a running horse and save it to /home/roshan/Downloads/horse.jpg"
        assert detect_requested_output_file(p1) == "/home/roshan/Downloads/horse.jpg"

        p2 = "draw a car and save to ~/Downloads/car.png"
        assert detect_requested_output_file(p2) == os.path.expanduser("~/Downloads/car.png")

        p3 = "please create a photo of a sunset to Downloads/sunset.webp"
        assert detect_requested_output_file(p3) == str(Path.home() / "Downloads/sunset.webp")

        p4 = "create a diagram and save as horse.jpg"
        assert detect_requested_output_file(p4) == str(Path.home() / "Downloads/horse.jpg")

    def test_is_image_task(self):
        assert is_image_task("generate an image of a running horse and save it to /home/roshan/Downloads/horse.jpg") is True
        assert is_image_task("draw a landscape in paint") is True
        assert is_image_task("render photo of mountain to mountain.png") is True
        assert is_image_task("fix the syntax error in apps/api/chat_api.py") is False
        assert is_image_task("run pytest tests/unit") is False


class TestSpokenTaskAnnouncements:
    def test_clean_spoken_text(self):
        raw = "```python\nprint(1)\n``` Check `file.py` at https://example.com/api key=secret_123"
        cleaned = clean_spoken_text(raw)
        assert "secret_123" not in cleaned
        assert "print(1)" not in cleaned
        assert "https://" not in cleaned
        assert "Check file.py at" in cleaned

    def test_make_completion_summary_image_success(self):
        summary = make_completion_summary(
            status="success",
            output_file="/home/roshan/Downloads/horse.jpg",
        )
        assert summary == "Task complete. I generated the image and saved it to Downloads as horse.jpg."

    def test_make_completion_summary_quota_failover_failure(self):
        summary = make_completion_summary(
            status="quota_exhausted",
            failover_trace=[
                {"step": "antigravity", "status": "failed", "reason": "429 RESOURCE_EXHAUSTED"},
                {"step": "freellmapi_images", "status": "failed", "reason": "HTTP 429 quota"},
            ],
            error="model quota is exhausted",
        )
        assert summary == "The task failed after trying Antigravity and FreeLLMAPI because the model quota is exhausted."

    @patch("apps.voice.service.voice_service")
    def test_announce_task_completion_enqueues_with_preempt(self, mock_vs):
        phrase = announce_task_completion(
            status="success",
            output_file="/home/roshan/Downloads/horse.jpg",
            auto_speak=True,
        )
        assert phrase == "Task complete. I generated the image and saved it to Downloads as horse.jpg."
        mock_vs.enqueue_response.assert_called_once_with(phrase, broadcast=True, preempt=True)


class TestCliBridgeFailover:
    def test_image_task_failover_to_freellmapi_on_primary_quota(self, monkeypatch):
        bridge = DeveloperCliBridge()
        # Mock PIN authorization
        monkeypatch.setattr(bridge, "verify_authorization", lambda pin: (True, "PIN verified"))

        # Mock detect_clis
        monkeypatch.setattr(bridge, "detect_clis", lambda force_refresh=False: {
            "antigravity": {"installed": True, "path": "/bin/agy"},
            "claude": {"installed": True, "path": "/bin/claude"},
            "primary": "antigravity",
        })

        # Mock primary CLI subprocess to return 429 quota exhaustion
        def mock_subprocess_run(cmd, *args, **kwargs):
            m = MagicMock()
            m.returncode = 0
            m.stdout = "429 RESOURCE_EXHAUSTED: Model quota reached."
            m.stderr = ""
            return m
        monkeypatch.setattr("subprocess.run", mock_subprocess_run)

        # Mock generate_image_via_freellmapi to succeed
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
            tf.write(b"IMAGEBYTES")
            tf.flush()
            saved_file = tf.name

        def mock_freellmapi(prompt, target_file=None, timeout=60):
            return {
                "status": "ok",
                "provider": "freellmapi_images",
                "output_file": saved_file,
                "size_bytes": 10,
                "output": f"Image successfully saved to {saved_file}",
            }
        monkeypatch.setattr(bridge, "generate_image_via_freellmapi", mock_freellmapi)

        # Mock voice announcer so it does not talk to real hardware
        monkeypatch.setattr("apps.voice.task_announcer.announce_task_completion", lambda **kwargs: "Mock announcement")

        res = bridge.execute_remediation(
            action="run_cli",
            pin="1234",
            cli="auto",
            prompt=f"generate an image of a running horse and save it to {saved_file}",
        )

        try:
            assert res["status"] == "ok"
            assert res["cli"] == "freellmapi_images"
            assert res["output_file"] == saved_file
            assert len(res["failover_trace"]) == 2
            assert res["failover_trace"][0]["step"] == "antigravity"
            assert res["failover_trace"][0]["status"] == "failed"
            assert res["failover_trace"][1]["step"] == "freellmapi_images"
            assert res["failover_trace"][1]["status"] == "success"
        finally:
            if os.path.exists(saved_file):
                os.unlink(saved_file)

    def test_image_task_quota_exhausted_when_all_fail(self, monkeypatch):
        bridge = DeveloperCliBridge()
        monkeypatch.setattr(bridge, "verify_authorization", lambda pin: (True, "PIN verified"))
        monkeypatch.setattr(bridge, "detect_clis", lambda force_refresh=False: {
            "antigravity": {"installed": True, "path": "/bin/agy"},
            "primary": "antigravity",
        })

        # Primary fails with 429
        def mock_subprocess_run(cmd, *args, **kwargs):
            m = MagicMock()
            m.returncode = 0
            m.stdout = "429 RESOURCE_EXHAUSTED"
            m.stderr = ""
            return m
        monkeypatch.setattr("subprocess.run", mock_subprocess_run)

        # FreeLLMAPI also fails
        def mock_freellmapi(prompt, target_file=None, timeout=60):
            return {
                "status": "error",
                "code": "HTTP_ERROR",
                "error": "HTTP 429 quota exhausted",
            }
        monkeypatch.setattr(bridge, "generate_image_via_freellmapi", mock_freellmapi)
        monkeypatch.setattr("apps.voice.task_announcer.announce_task_completion", lambda **kwargs: "Mock announcement")

        res = bridge.execute_remediation(
            action="run_cli",
            pin="1234",
            cli="auto",
            prompt="generate image of horse to /tmp/horse.jpg",
        )

        assert res["status"] == "error"
        assert res["code"] == "QUOTA_EXHAUSTED"
        assert "[FAILED" in res["output"]
        assert len(res["failover_trace"]) == 2
