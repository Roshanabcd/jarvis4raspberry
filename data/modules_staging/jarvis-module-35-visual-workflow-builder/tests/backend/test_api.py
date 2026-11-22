"""FastAPI REST & WebSocket API tests for JARVIS Module 35 — Visual Workflow Builder."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import WorkflowConfig
from backend.app.main import create_app


class TestWorkflowAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = WorkflowConfig(db_path=str(Path(self._tmp.name) / "api_workflows.db"))
        self.app = create_app(cfg)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_manifest_and_hud(self) -> None:
        r = self.client.get("/api/v1/workflows/health")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["module_id"], "jarvis-module-35-visual-workflow-builder")
        self.assertFalse(body["simulated"])

        m = self.client.get("/api/v1/workflows/manifest")
        self.assertEqual(m.status_code, 200)
        self.assertEqual(m.json()["default_port"], 8135)

        hud = self.client.get("/workflows")
        self.assertEqual(hud.status_code, 200)
        self.assertIn("Visual Workflow Builder", hud.text)

    def test_create_validate_execute_and_reject_cycle(self) -> None:
        payload = {
            "name": "Greeting Uppercase Flow",
            "description": "Uppercases input name and notifies",
            "nodes": [
                {"node_id": "t1", "node_type": "trigger", "label": "Trigger", "config": {}},
                {
                    "node_id": "u1",
                    "node_type": "transform",
                    "label": "Uppercase",
                    "config": {"operation": "uppercase", "input_key": "user", "output_key": "USER_CAPS"},
                },
                {
                    "node_id": "n1",
                    "node_type": "notify",
                    "label": "Notify",
                    "config": {"message": "Hello {USER_CAPS}"},
                },
            ],
            "edges": [
                {"source": "t1", "target": "u1"},
                {"source": "u1", "target": "n1"},
            ],
        }
        created = self.client.post("/api/v1/workflows/graphs", json=payload)
        self.assertEqual(created.status_code, 201)
        wf_id = created.json()["workflow_id"]

        val = self.client.post(f"/api/v1/workflows/graphs/{wf_id}/validate")
        self.assertEqual(val.status_code, 200)
        self.assertTrue(val.json()["valid"])
        self.assertEqual(val.json()["execution_order"], ["t1", "u1", "n1"])

        run = self.client.post(f"/api/v1/workflows/graphs/{wf_id}/execute", json={"input_data": {"user": "roshan"}})
        self.assertEqual(run.status_code, 201)
        self.assertEqual(run.json()["final_context"]["_notifications"], ["Hello ROSHAN"])

        # Cyclic workflow must return 422
        bad = self.client.post(
            "/api/v1/workflows/graphs",
            json={
                "name": "Bad Cycle",
                "nodes": [
                    {"node_id": "x", "node_type": "trigger", "label": "X", "config": {}},
                    {"node_id": "y", "node_type": "notify", "label": "Y", "config": {}},
                ],
                "edges": [{"source": "x", "target": "y"}, {"source": "y", "target": "x"}],
            },
        )
        self.assertEqual(bad.status_code, 422)
        self.assertEqual(bad.json()["error"]["code"], "WORKFLOW_CYCLE_DETECTED")

    def test_websocket_runs_channel(self) -> None:
        with self.client.websocket_connect("/api/v1/workflows/ws/runs") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")
            self.assertEqual(msg["status"]["adapter"], "local_dag_workflow_engine")
            self.assertFalse(msg["status"]["simulated"])


if __name__ == "__main__":
    unittest.main()
