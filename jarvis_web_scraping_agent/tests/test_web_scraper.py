"""Automated tests for JARVIS OS — Autonomous Web Scraping Agent (100% offline-testable)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from jarvis_web_scraping_agent.app import create_app
from jarvis_web_scraping_agent.config import WebScraperConfig


class TestWebScrapingAgent(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "web_scraper.db"
        self.config = WebScraperConfig(
            db_path=self.db_path,
            respect_robots_txt=True,
            allow_private_hosts=False,
        )
        self.app = create_app(config=self.config)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_ui_and_ssrf_blocking(self) -> None:
        health = self.client.get("/api/web-scraper/health")
        self.assertEqual(health.status_code, 200)
        self.assertTrue(health.json()["respect_robots_txt"])

        ui = self.client.get("/web-scraper")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("JARVIS OS — AUTONOMOUS WEB SCRAPING AGENT", ui.text)

        # SSRF / private IP & non-http schemes must be blocked with 403
        for bad_url in ("http://127.0.0.1:8000/admin", "http://localhost/secret", "file:///etc/passwd"):
            res = self.client.post("/api/web-scraper/extract", json={"url": bad_url})
            self.assertEqual(res.status_code, 403)

    def test_html_structure_extraction_and_json_export(self) -> None:
        sample_html = """
        <html>
          <head>
            <title>JARVIS Release Notes</title>
            <meta name="description" content="Official Raspberry Pi 5 releases" />
          </head>
          <body>
            <h1>Version 2.0</h1>
            <h2>Highlights</h2>
            <p>Added modular FastAPI features.</p>
            <a href="/docs">Documentation</a>
            <table>
              <tr><th>Module</th><th>Status</th></tr>
              <tr><td>AI Coding Assistant</td><td>Available</td></tr>
            </table>
            <script>console.log("ignore me");</script>
          </body>
        </html>
        """
        res = self.client.post(
            "/api/web-scraper/extract",
            json={
                "url": "https://example.org/releases",
                "raw_html": sample_html,
                "target_tag": "h2",
                "save_snapshot": True,
            },
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["title"], "JARVIS Release Notes")
        self.assertEqual(body["meta_description"], "Official Raspberry Pi 5 releases")
        self.assertIn("Version 2.0", body["headings"])
        self.assertEqual(body["links"][0]["href"], "https://example.org/docs")
        self.assertEqual(body["tables"][0][1], ["AI Coding Assistant", "Available"])
        self.assertEqual(body["targeted_elements"], ["Highlights"])
        self.assertNotIn("ignore me", body["text_preview"])

        # JSON Export
        snap_id = body["snapshot_id"]
        exp = self.client.get(f"/api/web-scraper/snapshots/{snap_id}/export")
        self.assertEqual(exp.status_code, 200)
        exported = json.loads(exp.text)
        self.assertEqual(exported["title"], "JARVIS Release Notes")

    def test_change_monitoring_and_diff_detection(self) -> None:
        mon = self.client.post(
            "/api/web-scraper/monitors",
            json={
                "name": "Status Monitor",
                "url": "https://example.org/status",
                "interval_minutes": 30,
            },
        )
        self.assertEqual(mon.status_code, 200)
        mon_id = mon.json()["id"]

        # First baseline check -> changed=False
        c1 = self.client.post(
            f"/api/web-scraper/monitors/{mon_id}/check",
            json={"raw_html_override": "<html><body><h1>Status</h1><p>Version 1.0 Online</p></body></html>"},
        )
        self.assertEqual(c1.status_code, 200)
        self.assertFalse(c1.json()["changed"])

        # Second check with identical HTML -> changed=False
        c2 = self.client.post(
            f"/api/web-scraper/monitors/{mon_id}/check",
            json={"raw_html_override": "<html><body><h1>Status</h1><p>Version 1.0 Online</p></body></html>"},
        )
        self.assertFalse(c2.json()["changed"])

        # Third check with updated content -> changed=True + unified diff
        c3 = self.client.post(
            f"/api/web-scraper/monitors/{mon_id}/check",
            json={"raw_html_override": "<html><body><h1>Status</h1><p>Version 2.0 Deployed</p></body></html>"},
        )
        self.assertTrue(c3.json()["changed"])
        self.assertIn("-Version 1.0 Online", c3.json()["unified_diff"])
        self.assertIn("+Version 2.0 Deployed", c3.json()["unified_diff"])


if __name__ == "__main__":
    unittest.main()
