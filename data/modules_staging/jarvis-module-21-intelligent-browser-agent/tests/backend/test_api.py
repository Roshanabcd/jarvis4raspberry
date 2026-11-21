"""FastAPI REST & WebSocket API tests for JARVIS Module 21."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import BrowserAgentConfig
from backend.app.main import create_app


class TestBrowserAgentAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = BrowserAgentConfig(
            db_path=str(Path(self._tmp.name) / "api_m21.db"),
            downloads_dir=str(Path(self._tmp.name) / "downloads"),
        )
        self.app = create_app(cfg)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.state.browser_agent.db.close()
        self._tmp.cleanup()

    def test_health_manifest_and_ui(self) -> None:
        h = self.client.get("/api/v1/browser-agent/health")
        self.assertEqual(h.status_code, 200)
        self.assertEqual(h.json()["module_id"], "jarvis-module-21-intelligent-browser-agent")
        self.assertTrue(h.json()["simulated"])

        m = self.client.get("/api/v1/browser-agent/manifest")
        self.assertEqual(m.status_code, 200)
        self.assertEqual(m.json()["module_number"], 21)

        ui = self.client.get("/browser-agent")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("INTELLIGENT BROWSER AGENT", ui.text)

    def test_session_navigation_ssrf_and_approval_flow(self) -> None:
        s_resp = self.client.post(
            "/api/v1/browser-agent/sessions",
            json={"name": "API Session", "start_url": "https://docs.jarvis.local/overview"},
        )
        self.assertEqual(s_resp.status_code, 201)
        sid = s_resp.json()["session_id"]

        # SSRF blocked with 403
        bad = self.client.post(f"/api/v1/browser-agent/sessions/{sid}/navigate", json={"url": "http://127.0.0.1:8121/"})
        self.assertEqual(bad.status_code, 403)

        # Navigate to feedback form and inspect DOM
        nav = self.client.post(
            f"/api/v1/browser-agent/sessions/{sid}/navigate",
            json={"url": "https://portal.jarvis.local/feedback"},
        )
        self.assertEqual(nav.status_code, 200)
        self.assertEqual(nav.json()["dom"]["element_counts"]["forms"], 1)

        # Fill and submit (queued for approval)
        fill = self.client.post(
            f"/api/v1/browser-agent/sessions/{sid}/form/fill",
            json={"form_id": "feedback-form", "fields": {"operator": "Roshan"}},
        )
        self.assertEqual(fill.status_code, 200)

        sub = self.client.post(
            f"/api/v1/browser-agent/sessions/{sid}/form/submit",
            json={"form_id": "feedback-form", "fields": {"operator": "Roshan"}, "requested_by": "test"},
        )
        self.assertEqual(sub.status_code, 200)
        self.assertEqual(sub.json()["status"], "awaiting_approval")
        approval_id = sub.json()["approval"]["approval_id"]

        # Decide approval
        dec = self.client.post(
            f"/api/v1/browser-agent/approvals/{approval_id}/decide",
            json={"approved": True, "decided_by": "operator", "comment": "LGTM"},
        )
        self.assertEqual(dec.status_code, 200)
        self.assertEqual(dec.json()["approval"]["status"], "approved")

        # Screenshot & close
        shot = self.client.post(f"/api/v1/browser-agent/sessions/{sid}/screenshot")
        self.assertEqual(shot.status_code, 200)
        self.assertIn("image_b64", shot.json())

        closed = self.client.post(f"/api/v1/browser-agent/sessions/{sid}/close")
        self.assertEqual(closed.status_code, 200)
        self.assertEqual(closed.json()["status"], "closed")

    def test_websocket_connection(self) -> None:
        with self.client.websocket_connect("/api/v1/browser-agent/ws/events") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")
            self.assertIn("status", msg)


if __name__ == "__main__":
    unittest.main()
