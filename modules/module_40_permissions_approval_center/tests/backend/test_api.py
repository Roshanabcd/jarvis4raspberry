"""FastAPI REST & WebSocket API tests for JARVIS Module 40 — Permissions & Approval Center."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from modules.module_40_permissions_approval_center.backend.app.config import ApprovalConfig
from modules.module_40_permissions_approval_center.backend.app.main import create_app


class TestApprovalAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = ApprovalConfig(db_path=str(Path(self._tmp.name) / "api_approvals.db"))
        self.app = create_app(cfg)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_manifest_and_hud(self) -> None:
        r = self.client.get("/api/v1/approvals/health")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["module_id"], "jarvis-module-40-permissions-approval-center")
        self.assertFalse(body["simulated"])

        m = self.client.get("/api/v1/approvals/manifest")
        self.assertEqual(m.status_code, 200)
        self.assertEqual(m.json()["default_port"], 8140)

        hud = self.client.get("/approvals")
        self.assertEqual(hud.status_code, 200)
        self.assertIn("Permissions &amp; Approval Center", hud.text)

    def test_policy_submit_decide_and_conflict(self) -> None:
        pol = self.client.post(
            "/api/v1/approvals/policies",
            json={"module_id": "m27", "action": "push_tag", "risk_level": "high", "mode": "require_approval"},
        )
        self.assertEqual(pol.status_code, 201)

        req = self.client.post(
            "/api/v1/approvals/requests",
            json={
                "requester": "ci-bot",
                "module_id": "m27",
                "action": "push_tag",
                "risk_level": "high",
                "summary": "Tag v1.0.0",
            },
        )
        self.assertEqual(req.status_code, 201)
        req_id = req.json()["request_id"]
        self.assertEqual(req.json()["status"], "pending")

        dec = self.client.post(
            f"/api/v1/approvals/requests/{req_id}/decide",
            json={"decision": "approve", "reviewer": "Roshan Sharma", "rationale": "LGTM"},
        )
        self.assertEqual(dec.status_code, 200)
        self.assertEqual(dec.json()["status"], "approved")

        dup = self.client.post(
            f"/api/v1/approvals/requests/{req_id}/decide",
            json={"decision": "deny", "reviewer": "Roshan Sharma"},
        )
        self.assertEqual(dup.status_code, 409)
        self.assertEqual(dup.json()["error"]["code"], "REQUEST_ALREADY_DECIDED")

    def test_websocket_requests_channel(self) -> None:
        with self.client.websocket_connect("/api/v1/approvals/ws/requests") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")
            self.assertEqual(msg["status"]["adapter"], "local_policy_approval_engine")
            self.assertFalse(msg["status"]["simulated"])


if __name__ == "__main__":
    unittest.main()
