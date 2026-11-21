"""Unit tests for JARVIS Module 21 — IntelligentBrowserEngine, DOM extraction & SSRF policy."""

from __future__ import annotations

import base64
import tempfile
import unittest
from pathlib import Path

from backend.adapters.browser_adapter import extract_dom
from backend.app.config import BrowserAgentConfig
from backend.services.browser_engine import BrowserAgentError, IntelligentBrowserEngine


class TestBrowserEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.cfg = BrowserAgentConfig(
            db_path=str(Path(self._tmp.name) / "test_m21.db"),
            downloads_dir=str(Path(self._tmp.name) / "downloads"),
        )
        self.engine = IntelligentBrowserEngine(self.cfg)

    def tearDown(self) -> None:
        self.engine.db.close()
        self._tmp.cleanup()

    def test_dom_extraction_parses_real_html(self) -> None:
        html = """
        <html><head><title>Sample Page</title></head><body>
          <h1>Main Heading</h1><h2>Sub Heading</h2>
          <a href="https://docs.jarvis.local/overview">Overview</a>
          <form id="login" action="/auth" method="POST">
            <input name="user" type="text" placeholder="Username" />
            <textarea name="bio"></textarea>
          </form>
        </body></html>
        """
        dom = extract_dom(html)
        self.assertEqual(dom["title"], "Sample Page")
        self.assertEqual(dom["element_counts"]["headings"], 2)
        self.assertEqual(dom["element_counts"]["links"], 1)
        self.assertEqual(dom["element_counts"]["forms"], 1)
        self.assertEqual(dom["forms"][0]["id"], "login")
        self.assertEqual(len(dom["forms"][0]["inputs"]), 2)

    def test_ssrf_and_site_policy_blocking(self) -> None:
        session = self.engine.create_session("Policy Test", "https://docs.jarvis.local/overview")
        sid = session["session_id"]
        for bad_url in [
            "http://127.0.0.1:8121/admin",
            "http://localhost/secret",
            "http://169.254.169.254/latest/meta-data/",
            "http://192.168.1.1/router",
            "file:///etc/passwd",
            "https://untrusted.evil.test/page",
        ]:
            with self.assertRaises(BrowserAgentError):
                self.engine.navigate(sid, bad_url)

    def test_screenshot_capture_and_download_sandbox(self) -> None:
        session = self.engine.create_session("Media Test", "https://releases.jarvis.local/downloads")
        sid = session["session_id"]
        shot = self.engine.screenshot_and_analyze(sid)
        self.assertTrue(shot["simulated"])
        self.assertGreater(shot["width"], 0)
        self.assertGreater(shot["height"], 0)
        raw_png = base64.b64decode(shot["image_b64"])
        self.assertTrue(raw_png.startswith(b"\x89PNG"))

        dl = self.engine.download_file(
            sid, "https://releases.jarvis.local/files/jarvis_release_notes.txt"
        )
        saved_file = self.engine.downloads_root / dl["filename"]
        self.assertTrue(saved_file.is_file())
        self.assertEqual(len(dl["sha256"]), 64)
        self.assertGreater(dl["size_bytes"], 10)

    def test_form_approval_gate_and_workflow_resume(self) -> None:
        wf = self.engine.run_workflow(
            "Feedback & Download Workflow",
            [
                {"action": "navigate", "params": {"url": "https://portal.jarvis.local/feedback"}},
                {
                    "action": "submit_form",
                    "params": {
                        "form_id": "feedback-form",
                        "fields": {"operator": "Roshan", "module": "21", "notes": "Test"},
                    },
                },
                {"action": "download", "params": {"url": "https://releases.jarvis.local/files/jarvis_release_notes.txt"}},
            ],
        )
        self.assertEqual(wf["status"], "awaiting_approval")
        approval_id = wf["results"][-1]["approval_id"]
        self.assertTrue(approval_id.startswith("bap_"))

        resumed = self.engine.decide_approval(approval_id, approved=True, decided_by="roshan")
        self.assertEqual(resumed["approval"]["status"], "approved")
        self.assertEqual(resumed["workflow"]["status"], "completed")
        self.assertEqual(len(self.engine.db.list_downloads()), 1)

    def test_workflow_cancellation(self) -> None:
        wf = self.engine.run_workflow(
            "Cancelable Workflow",
            [
                {"action": "navigate", "params": {"url": "https://portal.jarvis.local/feedback"}},
                {"action": "submit_form", "params": {"form_id": "feedback-form", "fields": {"operator": "Test"}}},
            ],
        )
        self.assertEqual(wf["status"], "awaiting_approval")
        cancelled = self.engine.cancel_workflow(wf["task_id"])
        self.assertEqual(cancelled["status"], "cancelled")


if __name__ == "__main__":
    unittest.main()
