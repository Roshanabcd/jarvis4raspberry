"""Unit tests for Module 40 ApprovalEngine (fail-closed policies, single-decision lock, TTL expiry)."""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from backend.app.config import ApprovalConfig
from backend.services.approval_engine import ApprovalEngine, ApprovalError


class TestApprovalEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = ApprovalConfig(db_path=str(Path(self._tmp.name) / "approvals.db"))
        self.engine = ApprovalEngine(config=cfg)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_policy_modes_auto_allow_auto_deny_and_fail_closed(self) -> None:
        self.engine.upsert_policy({"module_id": "m32", "action": "read", "risk_level": "low", "mode": "auto_allow"})
        self.engine.upsert_policy({"module_id": "m33", "action": "disable_fw", "risk_level": "critical", "mode": "auto_deny"})

        r_allow = self.engine.submit_request({"requester": "bot", "module_id": "m32", "action": "read", "risk_level": "low", "summary": "Read CPU"})
        self.assertEqual(r_allow["status"], "approved")

        r_deny = self.engine.submit_request({"requester": "bot", "module_id": "m33", "action": "disable_fw", "risk_level": "critical", "summary": "Drop FW"})
        self.assertEqual(r_deny["status"], "denied")

        r_unknown = self.engine.submit_request({"requester": "bot", "module_id": "m27", "action": "deploy", "risk_level": "high", "summary": "Deploy"})
        self.assertEqual(r_unknown["status"], "pending")

    def test_single_decision_lock_blocks_double_decision(self) -> None:
        req = self.engine.submit_request(
            {"requester": "agent", "module_id": "m29", "action": "delete_dir", "risk_level": "high", "summary": "Delete temp"}
        )
        decided = self.engine.decide_request(req["request_id"], "approve", "Roshan Sharma", "Safe path")
        self.assertEqual(decided["status"], "approved")

        with self.assertRaises(ApprovalError) as err:
            self.engine.decide_request(req["request_id"], "deny", "Roshan Sharma", "Changed mind")
        self.assertEqual(err.exception.code, "REQUEST_ALREADY_DECIDED")
        self.assertEqual(err.exception.status_code, 409)

    def test_ttl_expiration_returns_410_and_marks_expired(self) -> None:
        req = self.engine.submit_request(
            {"requester": "agent", "module_id": "m30", "action": "unlock_door", "risk_level": "critical", "summary": "Unlock", "ttl_seconds": 0}
        )
        time.sleep(0.02)
        with self.assertRaises(ApprovalError) as err:
            self.engine.decide_request(req["request_id"], "approve", "Roshan Sharma")
        self.assertEqual(err.exception.code, "REQUEST_EXPIRED")
        self.assertEqual(err.exception.status_code, 410)

        reloaded = self.engine.db.get_request(req["request_id"])
        assert reloaded is not None
        self.assertEqual(reloaded["status"], "expired")
        self.assertFalse(self.engine.get_status()["simulated"])


if __name__ == "__main__":
    unittest.main()
