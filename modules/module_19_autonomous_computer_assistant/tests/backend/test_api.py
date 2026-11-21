"""FastAPI REST & WebSocket API tests for Module 19."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from modules.module_19_autonomous_computer_assistant.backend.app.config import ComputerAssistantConfig
from modules.module_19_autonomous_computer_assistant.backend.app.main import create_app


class TestComputerAssistantAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = ComputerAssistantConfig(
            db_path=str(Path(self._tmp.name) / "api19.db"),
            sandbox_dir=str(Path(self._tmp.name) / "sandbox"),
        )
        self.app = create_app(config=cfg)
        self.ctx = TestClient(self.app)
        self.client = self.ctx.__enter__()

    def tearDown(self) -> None:
        self.ctx.__exit__(None, None, None)
        self._tmp.cleanup()

    def test_health_manifest_ui_and_diagnostics(self) -> None:
        self.assertEqual(self.client.get("/api/v1/computer-assistant/health").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/computer-assistant/manifest").json()["module_number"], 19)
        ui = self.client.get("/computer-assistant")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("AUTONOMOUS COMPUTER ASSISTANT", ui.text)
        self.assertEqual(self.client.get("/api/v1/computer-assistant/diagnostics").status_code, 200)

    def test_actions_approvals_estop_and_websocket(self) -> None:
        r_shot = self.client.post("/api/v1/computer-assistant/actions", json={"action_type": "capture_screenshot", "params": {}})
        self.assertEqual(r_shot.status_code, 201)
        shot_id = r_shot.json()["result"]["screenshot_id"]
        self.assertEqual(self.client.get(f"/api/v1/computer-assistant/screenshots/{shot_id}").status_code, 200)

        r_launch = self.client.post("/api/v1/computer-assistant/actions", json={"action_type": "launch_app", "params": {"app_id": "notes-pad"}})
        self.assertEqual(r_launch.status_code, 201)
        self.assertEqual(r_launch.json()["status"], "awaiting_approval")
        apr_id = r_launch.json()["approval"]["approval_id"]

        r_dec = self.client.post(f"/api/v1/computer-assistant/approvals/{apr_id}/decide", json={"approved": True, "decided_by": "test"})
        self.assertEqual(r_dec.status_code, 200)
        self.assertEqual(r_dec.json()["action"]["status"], "executed")

        self.assertEqual(self.client.post("/api/v1/computer-assistant/safety/estop", json={"reason": "test"}).status_code, 200)
        blocked = self.client.post("/api/v1/computer-assistant/actions", json={"action_type": "discover_apps", "params": {}})
        self.assertEqual(blocked.status_code, 423)
        self.assertEqual(self.client.post("/api/v1/computer-assistant/safety/estop/reset").status_code, 200)

        with self.client.websocket_connect("/api/v1/computer-assistant/ws/events") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")


if __name__ == "__main__":
    unittest.main()
