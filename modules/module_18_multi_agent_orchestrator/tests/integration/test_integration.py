"""Integration tests: full 4-stage demo DAG, manifest contract, adapter harness, and restart persistence."""

from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from modules.module_18_multi_agent_orchestrator.backend.app.config import OrchestratorConfig
from modules.module_18_multi_agent_orchestrator.backend.app.main import create_app
from modules.module_18_multi_agent_orchestrator.backend.models.database import OrchestratorDatabase
from modules.module_18_multi_agent_orchestrator.backend.services.orchestrator import MultiAgentOrchestrator

ROOT = Path(__file__).resolve().parents[2]


class TestModule18Integration(unittest.TestCase):
    def test_manifest_contract_completeness(self) -> None:
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        for key in (
            "module_id",
            "module_number",
            "name",
            "version",
            "contract_version",
            "category",
            "dependencies",
            "permissions",
            "resource_requirements",
            "entrypoints",
            "configuration_schema",
            "events",
            "error_format",
        ):
            self.assertIn(key, manifest, f"Missing required manifest field: {key}")
        self.assertEqual(manifest["module_number"], 18)

    def test_full_demo_workflow_and_approval_via_api(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = OrchestratorConfig(db_path=str(Path(tmp) / "int.db"), poll_interval_sec=0.03)
            app = create_app(config=cfg)
            with TestClient(app) as client:
                r = client.post("/api/v1/orchestrator/demo/launch")
                self.assertEqual(r.status_code, 201)
                wf_id = r.json()["workflow_id"]
                t4_id = r.json()["tasks"][3]["task_id"]

                # Wait for gated task t4 to reach awaiting_approval
                reached = False
                for _ in range(80):
                    st = client.get(f"/api/v1/orchestrator/tasks/{t4_id}").json()["status"]
                    if st == "awaiting_approval":
                        reached = True
                        break
                    time.sleep(0.04)
                self.assertTrue(reached, "Demo task 4 did not reach awaiting_approval")

                approvals = client.get("/api/v1/orchestrator/approvals?status=pending").json()["approvals"]
                self.assertGreaterEqual(len(approvals), 1)
                apr_id = approvals[0]["approval_id"]

                dec = client.post(
                    f"/api/v1/orchestrator/approvals/{apr_id}/decide",
                    json={"approved": True, "decided_by": "integration-test", "comment": "Looks good"},
                )
                self.assertEqual(dec.status_code, 200)

                completed = False
                for _ in range(80):
                    agg = client.get(f"/api/v1/orchestrator/workflows/{wf_id}/aggregate").json()
                    if agg["status"] == "completed":
                        completed = True
                        break
                    time.sleep(0.04)
                self.assertTrue(completed, "Demo workflow did not complete after approval")
                self.assertEqual(agg["total_tasks"], 4)
                self.assertEqual(agg["progress_percent"], 100.0)

    def test_sqlite_persistence_and_crash_recovery_across_restarts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "persist.db")
            db1 = OrchestratorDatabase(db_path)
            orch1 = MultiAgentOrchestrator(config=OrchestratorConfig(db_path=db_path), db=db1)
            # Insert a simulated interrupted running task directly into DB
            db1.create_task(
                {
                    "task_id": "tsk_interrupted",
                    "workflow_id": "wf-recover",
                    "title": "Interrupted Task",
                    "status": "running",
                    "priority": 3,
                    "created_at": "2026-11-20T00:00:00+00:00",
                    "updated_at": "2026-11-20T00:00:00+00:00",
                },
                [],
            )
            db1.close()

            # New orchestrator instance should recover it back to 'queued'
            orch2 = MultiAgentOrchestrator(config=OrchestratorConfig(db_path=db_path))
            recovered = orch2.db.get_task("tsk_interrupted")
            assert recovered is not None
            self.assertEqual(recovered["status"], "queued")
            orch2.db.close()


if __name__ == "__main__":
    unittest.main()
