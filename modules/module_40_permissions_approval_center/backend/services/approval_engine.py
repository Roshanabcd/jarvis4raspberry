"""Fail-Closed Permissions & Human-in-the-Loop Approval Engine (Module 40)."""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Optional

from modules.module_40_permissions_approval_center.backend.app.config import ApprovalConfig
from modules.module_40_permissions_approval_center.backend.models.database import ApprovalDB, utc_now_iso

VALID_RISK_LEVELS = {"low", "medium", "high", "critical"}
VALID_MODES = {"auto_allow", "require_approval", "auto_deny"}
VALID_DECISIONS = {"approve": "approved", "deny": "denied"}


class ApprovalError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class ApprovalEngine:
    adapter_name: str = "local_policy_approval_engine"
    is_simulated: bool = False

    def __init__(self, config: Optional[ApprovalConfig] = None, db: Optional[ApprovalDB] = None) -> None:
        self.config = config or ApprovalConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or ApprovalDB(self.config.db_path)
        self._started_at = time.monotonic()

    def _audit(self, request_id: str, actor: str, event_type: str, details: str) -> None:
        self.db.add_audit(
            {
                "event_id": f"aud_{uuid.uuid4().hex[:10]}",
                "request_id": request_id,
                "actor": actor,
                "event_type": event_type,
                "details": details,
                "created_at": utc_now_iso(),
            }
        )

    def upsert_policy(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        risk = payload.get("risk_level", "medium").strip().lower()
        mode = payload.get("mode", "require_approval").strip().lower()
        if risk not in VALID_RISK_LEVELS:
            raise ApprovalError("INVALID_RISK_LEVEL", f"Invalid risk_level '{risk}'.", 422)
        if mode not in VALID_MODES:
            raise ApprovalError("INVALID_POLICY_MODE", f"Invalid mode '{mode}'.", 422)
        return self.db.upsert_policy(
            {
                "policy_id": f"pol_{uuid.uuid4().hex[:10]}",
                "module_id": payload["module_id"].strip(),
                "action": payload["action"].strip(),
                "risk_level": risk,
                "mode": mode,
                "description": payload.get("description", "").strip(),
                "updated_at": utc_now_iso(),
            }
        )

    def submit_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        risk = payload.get("risk_level", "high").strip().lower()
        if risk not in VALID_RISK_LEVELS:
            raise ApprovalError("INVALID_RISK_LEVEL", f"Invalid risk_level '{risk}'.", 422)

        module_id = payload["module_id"].strip()
        action = payload["action"].strip()
        policy = self.db.get_policy(module_id, action)
        mode = policy["mode"] if policy else "require_approval"

        now_iso = utc_now_iso()
        now_epoch = time.time()
        ttl = int(payload.get("ttl_seconds", 600))
        req_id = f"apr_{uuid.uuid4().hex[:10]}"

        if mode == "auto_allow":
            status, reviewer, rationale, decided_at = "approved", "policy_engine", "Matched auto_allow policy", now_iso
        elif mode == "auto_deny":
            status, reviewer, rationale, decided_at = "denied", "policy_engine", "Matched auto_deny policy", now_iso
        else:
            status, reviewer, rationale, decided_at = "pending", None, None, None

        item = self.db.add_request(
            {
                "request_id": req_id,
                "requester": payload["requester"].strip(),
                "module_id": module_id,
                "action": action,
                "risk_level": risk,
                "summary": payload["summary"].strip(),
                "payload": payload.get("payload") or {},
                "status": status,
                "reviewer": reviewer,
                "rationale": rationale,
                "expires_at_epoch": now_epoch + ttl,
                "created_at": now_iso,
                "decided_at": decided_at,
            }
        )
        self._audit(req_id, payload["requester"].strip(), "request.submitted", f"{module_id}.{action} -> {status}")
        return item

    def decide_request(self, request_id: str, decision: str, reviewer: str, rationale: str = "") -> Dict[str, Any]:
        req = self.db.get_request(request_id)
        if not req:
            raise ApprovalError("REQUEST_NOT_FOUND", f"Approval request '{request_id}' not found.", 404)
        dec = decision.strip().lower()
        if dec not in VALID_DECISIONS:
            raise ApprovalError("INVALID_DECISION", "Decision must be 'approve' or 'deny'.", 422)
        if req["status"] != "pending":
            raise ApprovalError(
                "REQUEST_ALREADY_DECIDED",
                f"Request '{request_id}' is already finalized with status '{req['status']}'.",
                409,
            )
        if time.time() > float(req["expires_at_epoch"]):
            self.db.update_request_decision(request_id, "expired", "system_ttl", "Approval TTL expired", utc_now_iso())
            self._audit(request_id, "system_ttl", "request.expired", "TTL expired before decision")
            raise ApprovalError("REQUEST_EXPIRED", f"Request '{request_id}' has expired.", 410)

        new_status = VALID_DECISIONS[dec]
        updated = self.db.update_request_decision(
            request_id=request_id,
            status=new_status,
            reviewer=reviewer.strip(),
            rationale=rationale.strip(),
            decided_at=utc_now_iso(),
        )
        self._audit(request_id, reviewer.strip(), f"request.{new_status}", rationale.strip() or f"Marked {new_status}")
        return updated

    def get_status(self) -> Dict[str, Any]:
        reqs = self.db.list_requests(limit=500)
        pending = sum(1 for r in reqs if r["status"] == "pending")
        return {
            "adapter": self.adapter_name,
            "simulated": self.is_simulated,
            "policies_count": len(self.db.list_policies()),
            "requests_count": len(reqs),
            "pending_count": pending,
            "audit_events_count": len(self.db.list_audit(limit=500)),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
