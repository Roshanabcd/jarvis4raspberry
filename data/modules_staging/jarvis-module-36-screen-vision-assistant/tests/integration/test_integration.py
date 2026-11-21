"""Integration tests for mounting Module 36 inside a host JARVIS OS FastAPI app."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.config import VisionConfig
from backend.app.main import mount_module
from backend.services.vision_engine import VisionEngine


class TestModule36Integration(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = VisionConfig(db_path=str(Path(self._tmp.name) / "host_vision.db"))
        self.engine = VisionEngine(config=cfg)
        self.host_app = FastAPI(title="JARVIS OS Host")
        mount_module(self.host_app, engine=self.engine, include_root_ui=False)
        self.client = TestClient(self.host_app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_host_app_state_and_route_mounting(self) -> None:
        self.assertIs(self.host_app.state.vision, self.engine)
        status = self.client.get("/api/v1/vision/status")
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json()["adapter"], "local_screen_vision_engine")
        self.assertFalse(status.json()["simulated"])

    def test_end_to_end_capture_query_and_listing(self) -> None:
        created = self.client.post(
            "/api/v1/vision/captures",
            json={
                "title": "Terminal Window",
                "width": 800,
                "height": 600,
                "ocr_text": "uvicorn running on 8136",
                "elements": [
                    {"element_id": "term_1", "role": "terminal", "label": "Shell Output", "text": "8136", "x": 0, "y": 0, "width": 800, "height": 600, "confidence": 0.99}
                ],
            },
        )
        self.assertEqual(created.status_code, 201)
        cap_id = created.json()["capture_id"]

        self.client.post(f"/api/v1/vision/captures/{cap_id}/query", json={"question": "Show Shell Output"})
        queries = self.client.get(f"/api/v1/vision/queries?capture_id={cap_id}")
        self.assertEqual(queries.status_code, 200)
        self.assertEqual(queries.json()["count"], 1)

        caps = self.client.get("/api/v1/vision/captures")
        self.assertEqual(caps.status_code, 200)
        self.assertEqual(caps.json()["count"], 1)


if __name__ == "__main__":
    unittest.main()
