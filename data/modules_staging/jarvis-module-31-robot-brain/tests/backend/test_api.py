"""FastAPI REST & WebSocket tests for JARVIS Module 31 — JARVIS Robot Brain."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import RobotBrainConfig
from backend.app.main import create_app


class TestRobotBrainAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = RobotBrainConfig(db_path=str(Path(self._tmp.name) / "api_m31.db"))
        self.app = create_app(cfg)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_manifest_and_ui_route(self) -> None:
        h = self.client.get("/api/v1/robot-brain/health")
        self.assertEqual(h.status_code, 200)
        self.assertEqual(h.json()["module_id"], "jarvis-module-31-robot-brain")
        self.assertTrue(h.json()["simulated"])

        m = self.client.get("/api/v1/robot-brain/manifest")
        self.assertEqual(m.status_code, 200)
        self.assertEqual(m.json()["default_port"], 8131)

        ui = self.client.get("/robot-brain")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("ROBOT BRAIN", ui.text)

    def test_estop_and_motion_endpoints(self) -> None:
        e = self.client.post("/api/v1/robot-brain/estop", json={"reason": "API test"})
        self.assertEqual(e.status_code, 200)
        self.assertTrue(e.json()["estop_engaged"])

        blocked = self.client.post(
            "/api/v1/robot-brain/motion/cmd",
            json={"linear_mps": 0.5, "angular_rps": 0.0, "duration_s": 1.0},
        )
        self.assertEqual(blocked.status_code, 409)
        self.assertEqual(blocked.json()["error"]["code"], "ESTOP_ENGAGED")

        bad_reset = self.client.post("/api/v1/robot-brain/estop/reset", json={"confirm_reset": False})
        self.assertEqual(bad_reset.status_code, 409)

        ok_reset = self.client.post("/api/v1/robot-brain/estop/reset", json={"confirm_reset": True})
        self.assertEqual(ok_reset.status_code, 200)
        self.assertFalse(ok_reset.json()["estop_engaged"])

        moved = self.client.post(
            "/api/v1/robot-brain/motion/cmd",
            json={"linear_mps": 0.8, "angular_rps": 0.0, "duration_s": 1.0},
        )
        self.assertEqual(moved.status_code, 200)
        self.assertEqual(moved.json()["x"], 0.8)

    def test_websocket_telemetry_stream(self) -> None:
        with self.client.websocket_connect("/api/v1/robot-brain/ws/telemetry") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")
            self.assertIn("status", msg)


if __name__ == "__main__":
    unittest.main()
