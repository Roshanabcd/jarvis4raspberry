"""FastAPI REST & WebSocket tests for JARVIS Module 33 — Defensive Cybersecurity Agent."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import CyberSecurityConfig
from backend.app.main import create_app


class TestCyberSecurityAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.scan_root = Path(self._tmp.name) / "scan_root"
        self.scan_root.mkdir()
        cfg = CyberSecurityConfig(
            db_path=str(Path(self._tmp.name) / "api_m33.db"),
            scan_root=str(self.scan_root),
        )
        self.app = create_app(cfg)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_manifest_and_ui_route(self) -> None:
        h = self.client.get("/api/v1/cybersecurity/health")
        self.assertEqual(h.status_code, 200)
        self.assertEqual(h.json()["module_id"], "jarvis-module-33-defensive-cybersecurity-agent")
        self.assertFalse(h.json()["simulated"])

        m = self.client.get("/api/v1/cybersecurity/manifest")
        self.assertEqual(m.status_code, 200)
        self.assertEqual(m.json()["default_port"], 8133)

        ui = self.client.get("/cybersecurity")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("DEFENSIVE CYBERSECURITY", ui.text)

    def test_sandbox_guard_and_log_analysis_endpoints(self) -> None:
        bad = self.client.post("/api/v1/cybersecurity/scan/secrets", json={"relative_path": "../.."})
        self.assertEqual(bad.status_code, 403)
        self.assertEqual(bad.json()["error"]["code"], "PATH_OUTSIDE_SANDBOX")

        res = self.client.post(
            "/api/v1/cybersecurity/logs/analyze",
            json={
                "source": "nginx.log",
                "lines": ["GET /../../etc/passwd HTTP/1.1"],
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["incidents_created"], 1)
        inc_id = res.json()["incidents"][0]["incident_id"]

        resolved = self.client.post(
            f"/api/v1/cybersecurity/incidents/{inc_id}/resolve",
            json={"resolution_note": "Verified WAF blocked path traversal"},
        )
        self.assertEqual(resolved.status_code, 200)
        self.assertEqual(resolved.json()["status"], "resolved")

    def test_websocket_alerts_stream(self) -> None:
        with self.client.websocket_connect("/api/v1/cybersecurity/ws/alerts") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")
            self.assertIn("status", msg)


if __name__ == "__main__":
    unittest.main()
