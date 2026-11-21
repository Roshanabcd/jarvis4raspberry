"""Integration tests for mounting Module 35 inside a host JARVIS OS FastAPI app."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.config import WorkflowConfig
from backend.app.main import mount_module
from backend.services.workflow_engine import WorkflowEngine


class TestModule35Integration(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = WorkflowConfig(db_path=str(Path(self._tmp.name) / "host_workflows.db"))
        self.engine = WorkflowEngine(config=cfg)
        self.host_app = FastAPI(title="JARVIS OS Host")
        mount_module(self.host_app, engine=self.engine, include_root_ui=False)
        self.client = TestClient(self.host_app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_host_app_state_and_route_mounting(self) -> None:
        self.assertIs(self.host_app.state.workflows, self.engine)
        status = self.client.get("/api/v1/workflows/status")
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json()["adapter"], "local_dag_workflow_engine")
        self.assertFalse(status.json()["simulated"])

    def test_end_to_end_graph_execution_and_run_history(self) -> None:
        created = self.client.post(
            "/api/v1/workflows/graphs",
            json={
                "name": "Temp Conversion",
                "description": "Adds offset and emits notification",
                "nodes": [
                    {"node_id": "start", "node_type": "trigger", "label": "Start", "config": {}},
                    {
                        "node_id": "calc",
                        "node_type": "math",
                        "label": "Add 10",
                        "config": {"operation": "add", "a_key": "base", "b": 10, "output_key": "total"},
                    },
                ],
                "edges": [{"source": "start", "target": "calc"}],
            },
        )
        self.assertEqual(created.status_code, 201)
        wf_id = created.json()["workflow_id"]

        run = self.client.post(f"/api/v1/workflows/graphs/{wf_id}/execute", json={"input_data": {"base": 32}})
        self.assertEqual(run.status_code, 201)
        self.assertEqual(run.json()["final_context"]["total"], 42.0)

        runs = self.client.get(f"/api/v1/workflows/runs?workflow_id={wf_id}")
        self.assertEqual(runs.status_code, 200)
        self.assertEqual(runs.json()["count"], 1)

        graphs = self.client.get("/api/v1/workflows/graphs")
        self.assertEqual(graphs.status_code, 200)
        self.assertEqual(graphs.json()["count"], 1)


if __name__ == "__main__":
    unittest.main()
