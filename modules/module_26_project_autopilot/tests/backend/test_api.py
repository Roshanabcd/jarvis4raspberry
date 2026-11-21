"""REST & WebSocket API tests for JARVIS Module 26 — Project Autopilot."""

from __future__ import annotations

import os
import tempfile
import unittest

from fastapi.testclient import TestClient

from modules.module_26_project_autopilot.backend.app.config import ProjectAutopilotConfig
from modules.module_26_project_autopilot.backend.app.main import create_app


class TestProjectAutopilotAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = ProjectAutopilotConfig(
            db_path=os.path.join(self._tmp.name, "api_m26.db"),
            workspace_root=os.path.join(self._tmp.name, "workspaces"),
        )
        self.app = create_app(config=cfg)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_manifest_status_and_ui(self) -> None:
        r_health = self.client.get("/api/v1/project-autopilot/health")
        self.assertEqual(r_health.status_code, 200)
        self.assertEqual(r_health.json()["module_id"], "jarvis-module-26-project-autopilot")
        self.assertTrue(r_health.json()["simulated"])

        r_manifest = self.client.get("/api/v1/project-autopilot/manifest")
        self.assertEqual(r_manifest.status_code, 200)
        self.assertEqual(r_manifest.json()["version"], "1.0.0")

        r_ui = self.client.get("/project-autopilot")
        self.assertEqual(r_ui.status_code, 200)
        self.assertIn("Project Autopilot", r_ui.text)

    def test_full_rest_workflow_with_approval_and_scaffold(self) -> None:
        cr = self.client.post(
            "/api/v1/project-autopilot/projects",
            json={
                "name": "Autonomous CI Worker",
                "goal": "Run lightweight CI checks and report pass/fail status.",
                "tech_stack": ["Python", "FastAPI"],
                "dry_run": True,
                "auto_plan": True,
            },
        )
        self.assertEqual(cr.status_code, 201)
        pid = cr.json()["project"]["project_id"]

        adv1 = self.client.post(f"/api/v1/project-autopilot/projects/{pid}/advance", json={"max_steps": 10})
        self.assertEqual(adv1.status_code, 200)
        self.assertEqual(adv1.json()["executed_count"], 4)

        appr_list = self.client.get("/api/v1/project-autopilot/approvals", params={"project_id": pid})
        self.assertEqual(appr_list.status_code, 200)
        self.assertEqual(appr_list.json()["count"], 1)
        gated_id = appr_list.json()["approvals"][0]["task_id"]

        dec = self.client.post(
            f"/api/v1/project-autopilot/tasks/{gated_id}/approval",
            json={"decision": "approve", "reviewer": "roshan", "note": "Approved"},
        )
        self.assertEqual(dec.status_code, 200)
        self.assertEqual(dec.json()["status"], "approved")

        adv2 = self.client.post(f"/api/v1/project-autopilot/projects/{pid}/advance", json={"max_steps": 5})
        self.assertEqual(adv2.status_code, 200)
        self.assertEqual(adv2.json()["progress_pct"], 100.0)

        scaf = self.client.post(f"/api/v1/project-autopilot/projects/{pid}/scaffold", json={"include_tests": True})
        self.assertEqual(scaf.status_code, 201)
        self.assertIn("README.md", scaf.json()["created_files"])

        bp = self.client.get(f"/api/v1/project-autopilot/projects/{pid}/blueprint.md")
        self.assertEqual(bp.status_code, 200)
        self.assertIn("# Project Autopilot Blueprint: Autonomous CI Worker", bp.text)

    def test_websocket_connects(self) -> None:
        with self.client.websocket_connect("/api/v1/project-autopilot/ws/events") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")
            self.assertIn("status", msg)


if __name__ == "__main__":
    unittest.main()
