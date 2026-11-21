"""FastAPI REST & WebSocket API contract tests for JARVIS Module 18."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from modules.module_18_multi_agent_orchestrator.backend.app.config import OrchestratorConfig
from modules.module_18_multi_agent_orchestrator.backend.app.main import create_app


class TestOrchestratorAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = OrchestratorConfig(
            db_path=str(Path(self._tmp.name) / "api_test.db"),
            max_concurrency=4,
            poll_interval_sec=0.03,
        )
        self.app = create_app(config=cfg)
        self.client_ctx = TestClient(self.app)
        self.client = self.client_ctx.__enter__()

    def tearDown(self) -> None:
        self.client_ctx.__exit__(None, None, None)
        self._tmp.cleanup()

    def test_health_manifest_and_ui_routes(self) -> None:
        r_health = self.client.get("/api/v1/orchestrator/health")
        self.assertEqual(r_health.status_code, 200)
        body = r_health.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["module_id"], "jarvis-module-18-multi-agent-orchestrator")
        self.assertFalse(body["core_adapter"]["connected_to_jarvis_core"])

        r_manifest = self.client.get("/api/v1/orchestrator/manifest")
        self.assertEqual(r_manifest.status_code, 200)
        self.assertEqual(r_manifest.json()["module_number"], 18)

        r_ui = self.client.get("/orchestrator")
        self.assertEqual(r_ui.status_code, 200)
        self.assertIn("MULTI-AGENT ORCHESTRATOR", r_ui.text)

    def test_agent_crud_and_validation(self) -> None:
        r_list = self.client.get("/api/v1/orchestrator/agents")
        self.assertEqual(r_list.status_code, 200)
        self.assertGreaterEqual(r_list.json()["count"], 4)

        r_create = self.client.post(
            "/api/v1/orchestrator/agents",
            json={
                "name": "SENTINEL Custom",
                "role": "Audit Worker",
                "capabilities": ["code_analysis"],
                "handler_type": "code_analysis",
                "max_concurrency": 2,
            },
        )
        self.assertEqual(r_create.status_code, 201)
        agent_id = r_create.json()["agent_id"]

        r_patch = self.client.patch(f"/api/v1/orchestrator/agents/{agent_id}", json={"status": "paused"})
        self.assertEqual(r_patch.status_code, 200)
        self.assertEqual(r_patch.json()["status"], "paused")

        r_del = self.client.delete(f"/api/v1/orchestrator/agents/{agent_id}")
        self.assertEqual(r_del.status_code, 200)
        self.assertTrue(r_del.json()["deleted"])

        # Unknown handler returns structured error
        r_bad = self.client.post(
            "/api/v1/orchestrator/agents",
            json={"name": "Bad", "role": "None", "handler_type": "does_not_exist"},
        )
        self.assertEqual(r_bad.status_code, 422)
        self.assertEqual(r_bad.json()["error"]["code"], "UNKNOWN_HANDLER")

    def test_engine_controls_limits_messages_and_websocket(self) -> None:
        r_pause = self.client.post("/api/v1/orchestrator/engine/pause")
        self.assertEqual(r_pause.status_code, 200)
        self.assertTrue(r_pause.json()["paused"])

        r_lim = self.client.put("/api/v1/orchestrator/engine/limits", json={"max_concurrency": 6})
        self.assertEqual(r_lim.status_code, 200)
        self.assertEqual(r_lim.json()["max_concurrency"], 6)

        r_res = self.client.post("/api/v1/orchestrator/engine/resume")
        self.assertEqual(r_res.status_code, 200)
        self.assertFalse(r_res.json()["paused"])

        r_msg = self.client.post(
            "/api/v1/orchestrator/messages",
            json={"sender_agent_id": "operator", "recipient_agent_id": "broadcast", "content": "System check"},
        )
        self.assertEqual(r_msg.status_code, 201)

        with self.client.websocket_connect("/api/v1/orchestrator/ws/events") as ws:
            hello = ws.receive_json()
            self.assertEqual(hello["event_type"], "ws.connected")


if __name__ == "__main__":
    unittest.main()
