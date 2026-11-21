"""Integration tests for mounting Module 40 inside a host JARVIS OS FastAPI app."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.module_40_permissions_approval_center.backend.app.config import ApprovalConfig
from modules.module_40_permissions_approval_center.backend.app.main import mount_module
from modules.module_40_permissions_approval_center.backend.services.approval_engine import ApprovalEngine


class TestModule40Integration(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = ApprovalConfig(db_path=str(Path(self._tmp.name) / "host_approvals.db"))
        self.engine = ApprovalEngine(config=cfg)
        self.host_app = FastAPI(title="JARVIS OS Host")
        mount_module(self.host_app, engine=self.engine, include_root_ui=False)
        self.client = TestClient(self.host_app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_host_app_state_and_route_mounting(self) -> None:
        self.assertIs(self.host_app.state.approvals, self.engine)
        status = self.client.get("/api/v1/approvals/status")
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json()["adapter"], "local_policy_approval_engine")
        self.assertFalse(status.json()["simulated"])

    def test_end_to_end_pending_filter_and_audit(self) -> None:
        req = self.client.post(
            "/api/v1/approvals/requests",
            json={
                "requester": "workflow-engine",
                "module_id": "m39",
                "action": "restore_snapshot",
                "risk_level": "high",
                "summary": "Restore workspace snapshot",
            },
        ).json()

        pending = self.client.get("/api/v1/approvals/requests?status=pending")
        self.assertEqual(pending.status_code, 200)
        self.assertEqual(pending.json()["count"], 1)

        self.client.post(
            f"/api/v1/approvals/requests/{req['request_id']}/decide",
            json={"decision": "deny", "reviewer": "Roshan Sharma", "rationale": "Wrong target"},
        )
        audit = self.client.get("/api/v1/approvals/audit")
        self.assertEqual(audit.status_code, 200)
        self.assertEqual(audit.json()["count"], 2)


if __name__ == "__main__":
    unittest.main()
