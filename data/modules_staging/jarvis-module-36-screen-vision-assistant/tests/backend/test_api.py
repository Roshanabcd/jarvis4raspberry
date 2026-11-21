"""FastAPI REST & WebSocket API tests for JARVIS Module 36 — Screen Vision Assistant."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import VisionConfig
from backend.app.main import create_app


class TestVisionAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = VisionConfig(db_path=str(Path(self._tmp.name) / "api_vision.db"))
        self.app = create_app(cfg)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_manifest_and_hud(self) -> None:
        r = self.client.get("/api/v1/vision/health")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["module_id"], "jarvis-module-36-screen-vision-assistant")
        self.assertFalse(body["simulated"])

        m = self.client.get("/api/v1/vision/manifest")
        self.assertEqual(m.status_code, 200)
        self.assertEqual(m.json()["default_port"], 8136)

        hud = self.client.get("/vision")
        self.assertEqual(hud.status_code, 200)
        self.assertIn("Screen Vision Assistant", hud.text)

    def test_capture_hit_test_and_query_endpoints(self) -> None:
        created = self.client.post(
            "/api/v1/vision/captures",
            json={
                "title": "Dashboard Screen",
                "source": "desktop_primary",
                "width": 1000,
                "height": 600,
                "ocr_text": "Deploy | Settings",
                "elements": [
                    {"element_id": "btn_settings", "role": "button", "label": "Settings", "text": "Settings", "x": 800, "y": 20, "width": 150, "height": 50, "confidence": 0.98}
                ],
            },
        )
        self.assertEqual(created.status_code, 201)
        cap_id = created.json()["capture_id"]

        hit = self.client.post(f"/api/v1/vision/captures/{cap_id}/hit-test", json={"x": 850, "y": 40})
        self.assertEqual(hit.status_code, 200)
        self.assertEqual(hit.json()["count"], 1)
        self.assertEqual(hit.json()["hits"][0]["element_id"], "btn_settings")

        qa = self.client.post(f"/api/v1/vision/captures/{cap_id}/query", json={"question": "Find Settings button"})
        self.assertEqual(qa.status_code, 201)
        self.assertIn("Settings", qa.json()["answer"])

        bad_hit = self.client.post(f"/api/v1/vision/captures/{cap_id}/hit-test", json={"x": 1500, "y": 40})
        self.assertEqual(bad_hit.status_code, 422)
        self.assertEqual(bad_hit.json()["error"]["code"], "COORDINATE_OUT_OF_BOUNDS")

    def test_websocket_captures_channel(self) -> None:
        with self.client.websocket_connect("/api/v1/vision/ws/captures") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")
            self.assertEqual(msg["status"]["adapter"], "local_screen_vision_engine")
            self.assertFalse(msg["status"]["simulated"])


if __name__ == "__main__":
    unittest.main()
