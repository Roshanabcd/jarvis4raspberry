"""Runnable CLI demo for JARVIS Module 40 — Permissions & Approval Center."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.module_40_permissions_approval_center.backend.app.config import ApprovalConfig
from modules.module_40_permissions_approval_center.backend.services.approval_engine import ApprovalEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cfg = ApprovalConfig(db_path=str(Path(tmp) / "demo_approvals.db"))
        engine = ApprovalEngine(config=cfg)
        engine.upsert_policy(
            {
                "module_id": "module-32-health",
                "action": "read_metrics",
                "risk_level": "low",
                "mode": "auto_allow",
                "description": "Read-only telemetry",
            }
        )
        auto_req = engine.submit_request(
            {
                "requester": "dashboard",
                "module_id": "module-32-health",
                "action": "read_metrics",
                "risk_level": "low",
                "summary": "Fetch Pi 5 CPU temperature",
            }
        )
        gated_req = engine.submit_request(
            {
                "requester": "deploy-agent",
                "module_id": "module-27-github-cicd",
                "action": "deploy_prod",
                "risk_level": "critical",
                "summary": "Deploy production release",
            }
        )
        decided = engine.decide_request(gated_req["request_id"], "approve", "Roshan Sharma", "Verified green CI")
        print(
            json.dumps(
                {
                    "simulated": engine.is_simulated,
                    "auto_allow_status": auto_req["status"],
                    "gated_initial_status": gated_req["status"],
                    "gated_final_status": decided["status"],
                    "audit_events": len(engine.db.list_audit()),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
