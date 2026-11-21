"""Permission-controlled Autonomous Computer Assistant Engine (Module 19).

Safety guarantees:
1. Emergency Stop (E-STOP) persists in SQLite and blocks all actions until explicitly reset.
2. Dry-run mode validates permissions, risk, and parameters without mutating desktop or sandbox files.
3. High-risk actions (launch_app, keyboard_hotkey, file_write, file_delete) pause in
   AWAITING_APPROVAL until an operator approves or rejects them.
4. File I/O is strictly confined to `sandbox_dir` with canonical path-traversal checks.
5. Uses SafeDemoDesktopAdapter by default — never controls the real host OS.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from modules.module_19_autonomous_computer_assistant.backend.adapters.contracts import DesktopAutomationAdapter
from modules.module_19_autonomous_computer_assistant.backend.adapters.safe_demo_adapter import SafeDemoDesktopAdapter
from modules.module_19_autonomous_computer_assistant.backend.app.config import ComputerAssistantConfig
from modules.module_19_autonomous_computer_assistant.backend.models.database import ComputerAssistantDB, utc_now_iso
from modules.module_19_autonomous_computer_assistant.backend.models.schemas import ActionStatus, ActionType, RiskLevel


RISK_MATRIX: Dict[str, RiskLevel] = {
    ActionType.DISCOVER_APPS.value: RiskLevel.LOW,
    ActionType.CAPTURE_SCREENSHOT.value: RiskLevel.LOW,
    ActionType.SELECT_WINDOW.value: RiskLevel.LOW,
    ActionType.FILE_LIST.value: RiskLevel.LOW,
    ActionType.FILE_READ.value: RiskLevel.LOW,
    ActionType.MOUSE_MOVE.value: RiskLevel.MEDIUM,
    ActionType.MOUSE_CLICK.value: RiskLevel.MEDIUM,
    ActionType.KEYBOARD_TYPE.value: RiskLevel.MEDIUM,
    ActionType.KEYBOARD_HOTKEY.value: RiskLevel.HIGH,
    ActionType.LAUNCH_APP.value: RiskLevel.HIGH,
    ActionType.FILE_WRITE.value: RiskLevel.HIGH,
    ActionType.FILE_DELETE.value: RiskLevel.HIGH,
}

DEFAULT_POLICY: Dict[str, bool] = {
    "allow_screenshot": True,
    "allow_keyboard_mouse": True,
    "allow_app_launch": True,
    "allow_file_write": True,
    "require_approval_for_high_risk": True,
}


class AssistantError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class ComputerAssistantEngine:
    def __init__(
        self,
        config: Optional[ComputerAssistantConfig] = None,
        db: Optional[ComputerAssistantDB] = None,
        adapter: Optional[DesktopAutomationAdapter] = None,
    ) -> None:
        self.config = config or ComputerAssistantConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or ComputerAssistantDB(self.config.db_path)
        self.adapter = adapter or SafeDemoDesktopAdapter()
        self.sandbox_root = Path(self.config.sandbox_dir).resolve()
        self.sandbox_root.mkdir(parents=True, exist_ok=True)
        self._started_at = time.monotonic()

        # Seed a sample sandbox file if empty
        welcome_file = self.sandbox_root / "welcome_sandbox.txt"
        if not welcome_file.exists():
            welcome_file.write_text(
                "JARVIS OS Module 19 — Sandboxed File Workspace\nSafe local file interaction boundary.\n",
                encoding="utf-8",
            )

        self.estop_active: bool = self.db.get_state("estop_active", "false") == "true"
        self.estop_reason: str = self.db.get_state("estop_reason", "") or ""
        persisted_dry = self.db.get_state("dry_run_mode")
        self.dry_run_mode: bool = (
            persisted_dry == "true" if persisted_dry is not None else self.config.dry_run_default
        )
        raw_policy = self.db.get_state("permission_policy")
        self.policy: Dict[str, bool] = json.loads(raw_policy) if raw_policy else dict(DEFAULT_POLICY)

    # --- Safety Controls ---
    def engage_estop(self, reason: str, triggered_by: str = "operator") -> Dict[str, Any]:
        self.estop_active = True
        self.estop_reason = reason
        self.db.set_state("estop_active", "true")
        self.db.set_state("estop_reason", reason)
        self.db.add_log(
            event_type="computer.estop.engaged",
            level="WARNING",
            message=f"EMERGENCY STOP engaged by {triggered_by}: {reason}",
        )
        return self.get_status()

    def reset_estop(self, reset_by: str = "operator") -> Dict[str, Any]:
        self.estop_active = False
        self.estop_reason = ""
        self.db.set_state("estop_active", "false")
        self.db.set_state("estop_reason", "")
        self.db.add_log(
            event_type="computer.estop.reset",
            level="INFO",
            message=f"Emergency Stop cleared by {reset_by}.",
        )
        return self.get_status()

    def set_dry_run(self, enabled: bool) -> Dict[str, Any]:
        self.dry_run_mode = bool(enabled)
        self.db.set_state("dry_run_mode", "true" if self.dry_run_mode else "false")
        self.db.add_log(
            event_type="computer.dry_run.updated",
            message=f"Global dry-run mode set to {self.dry_run_mode}.",
        )
        return self.get_status()

    def update_policy(self, updates: Dict[str, Any]) -> Dict[str, bool]:
        for k, v in updates.items():
            if k in self.policy and v is not None:
                self.policy[k] = bool(v)
        self.db.set_state("permission_policy", json.dumps(self.policy))
        self.db.add_log(
            event_type="computer.policy.updated",
            message="Permission policy updated.",
            details=self.policy,
        )
        return dict(self.policy)

    # --- Sandboxed File Path Guard ---
    def _resolve_sandbox_path(self, rel_path: str) -> Path:
        if not rel_path or rel_path.startswith("/") or ".." in Path(rel_path).parts:
            raise AssistantError(
                "PATH_TRAVERSAL_BLOCKED",
                "Path must be relative and remain strictly within the configured sandbox directory.",
                403,
            )
        candidate = (self.sandbox_root / rel_path).resolve()
        try:
            candidate.relative_to(self.sandbox_root)
        except ValueError as exc:
            raise AssistantError(
                "PATH_TRAVERSAL_BLOCKED",
                "Resolved path escapes sandbox directory.",
                403,
            ) from exc
        return candidate

    # --- Permission Check ---
    def _check_policy_allowed(self, action_type: str) -> None:
        if action_type == ActionType.CAPTURE_SCREENSHOT.value and not self.policy["allow_screenshot"]:
            raise AssistantError("PERMISSION_DENIED", "Screenshot capture is disabled by permission policy.", 403)
        if action_type in (
            ActionType.MOUSE_MOVE.value,
            ActionType.MOUSE_CLICK.value,
            ActionType.KEYBOARD_TYPE.value,
            ActionType.KEYBOARD_HOTKEY.value,
        ) and not self.policy["allow_keyboard_mouse"]:
            raise AssistantError("PERMISSION_DENIED", "Keyboard/mouse actions are disabled by permission policy.", 403)
        if action_type == ActionType.LAUNCH_APP.value and not self.policy["allow_app_launch"]:
            raise AssistantError("PERMISSION_DENIED", "Application launch is disabled by permission policy.", 403)
        if action_type in (ActionType.FILE_WRITE.value, ActionType.FILE_DELETE.value) and not self.policy["allow_file_write"]:
            raise AssistantError("PERMISSION_DENIED", "File write/delete is disabled by permission policy.", 403)

    # --- Action Submission & Execution ---
    def submit_action(
        self,
        action_type: str,
        params: Dict[str, Any],
        dry_run: Optional[bool] = None,
        requested_by: str = "operator",
        reason: str = "",
        replayed_from: Optional[str] = None,
    ) -> Dict[str, Any]:
        risk = RISK_MATRIX.get(action_type, RiskLevel.HIGH)
        effective_dry_run = self.dry_run_mode if dry_run is None else bool(dry_run)
        action_id = f"act_{uuid.uuid4().hex[:10]}"
        now = utc_now_iso()

        if self.estop_active:
            rec = self.db.create_action(
                {
                    "action_id": action_id,
                    "action_type": action_type,
                    "risk_level": risk.value,
                    "status": ActionStatus.BLOCKED_ESTOP.value,
                    "dry_run": effective_dry_run,
                    "simulated": self.adapter.is_simulated,
                    "requested_by": requested_by,
                    "reason": reason,
                    "params": params,
                    "error": f"Blocked by Emergency Stop: {self.estop_reason}",
                    "replayed_from": replayed_from,
                    "created_at": now,
                    "updated_at": now,
                }
            )
            self.db.add_log(
                event_type="computer.action.blocked_estop",
                level="WARNING",
                action_id=action_id,
                message=f"Blocked '{action_type}' while E-STOP is active.",
            )
            raise AssistantError(
                "ESTOP_ACTIVE",
                f"Emergency Stop is active ({self.estop_reason}). Reset E-STOP before executing actions.",
                423,
                details={"action_id": rec["action_id"]},
            )

        self._check_policy_allowed(action_type)

        # Dry-run never mutates state or requires approval
        if effective_dry_run:
            # Still validate sandbox path if file action
            if action_type in (ActionType.FILE_READ.value, ActionType.FILE_WRITE.value, ActionType.FILE_DELETE.value):
                self._resolve_sandbox_path(str(params.get("path", "")))
            plan = {
                "dry_run": True,
                "simulated_adapter": self.adapter.is_simulated,
                "would_execute": action_type,
                "risk_level": risk.value,
                "requires_approval_in_live_run": risk == RiskLevel.HIGH and self.policy["require_approval_for_high_risk"],
                "validated_params": params,
            }
            rec = self.db.create_action(
                {
                    "action_id": action_id,
                    "action_type": action_type,
                    "risk_level": risk.value,
                    "status": ActionStatus.DRY_RUN.value,
                    "dry_run": True,
                    "simulated": self.adapter.is_simulated,
                    "requested_by": requested_by,
                    "reason": reason,
                    "params": params,
                    "result": plan,
                    "replayed_from": replayed_from,
                    "created_at": now,
                    "updated_at": now,
                }
            )
            self.db.add_log(
                event_type="computer.action.dry_run",
                action_id=action_id,
                message=f"Dry-run validated '{action_type}' (risk={risk.value}).",
            )
            return rec

        # High-risk human approval gate
        if risk == RiskLevel.HIGH and self.policy["require_approval_for_high_risk"]:
            rec = self.db.create_action(
                {
                    "action_id": action_id,
                    "action_type": action_type,
                    "risk_level": risk.value,
                    "status": ActionStatus.AWAITING_APPROVAL.value,
                    "dry_run": False,
                    "simulated": self.adapter.is_simulated,
                    "requested_by": requested_by,
                    "reason": reason,
                    "params": params,
                    "replayed_from": replayed_from,
                    "created_at": now,
                    "updated_at": now,
                }
            )
            approval = self.db.create_approval(
                {
                    "approval_id": f"cap_{uuid.uuid4().hex[:10]}",
                    "action_id": action_id,
                    "action_type": action_type,
                    "risk_level": risk.value,
                    "prompt": f"Approve HIGH-RISK computer action '{action_type}' requested by {requested_by}? params={params}",
                    "status": "pending",
                    "created_at": now,
                }
            )
            self.db.add_log(
                event_type="computer.action.awaiting_approval",
                level="WARNING",
                action_id=action_id,
                message=f"Action '{action_type}' paused for human approval ({approval['approval_id']}).",
            )
            return {**rec, "approval": approval}

        # Execute immediately (LOW/MEDIUM or approval gate disabled)
        rec = self.db.create_action(
            {
                "action_id": action_id,
                "action_type": action_type,
                "risk_level": risk.value,
                "status": ActionStatus.EXECUTED.value,
                "dry_run": False,
                "simulated": self.adapter.is_simulated,
                "requested_by": requested_by,
                "reason": reason,
                "params": params,
                "replayed_from": replayed_from,
                "created_at": now,
                "updated_at": now,
            }
        )
        return self._run_action_record(rec)

    def _run_action_record(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        t0 = time.perf_counter()
        action_id = rec["action_id"]
        atype = rec["action_type"]
        p = rec["params"]
        try:
            if atype == ActionType.DISCOVER_APPS.value:
                result: Any = {"apps": self.adapter.discover_applications()}
            elif atype == ActionType.CAPTURE_SCREENSHOT.value:
                shot = self.adapter.capture_screenshot(window_id=p.get("window_id"))
                shot["action_id"] = action_id
                self.db.save_screenshot(shot)
                result = {
                    "screenshot_id": shot["screenshot_id"],
                    "window_id": shot["window_id"],
                    "width": shot["width"],
                    "height": shot["height"],
                    "simulated": shot["simulated"],
                }
            elif atype == ActionType.SELECT_WINDOW.value:
                result = self.adapter.select_window(str(p.get("window_id", "")))
            elif atype == ActionType.MOUSE_MOVE.value:
                result = self.adapter.mouse_move(int(p.get("x", 0)), int(p.get("y", 0)))
            elif atype == ActionType.MOUSE_CLICK.value:
                result = self.adapter.mouse_click(
                    int(p.get("x", 0)),
                    int(p.get("y", 0)),
                    button=str(p.get("button", "left")),
                    clicks=int(p.get("clicks", 1)),
                )
            elif atype == ActionType.KEYBOARD_TYPE.value:
                result = self.adapter.keyboard_type(str(p.get("text", "")))
            elif atype == ActionType.KEYBOARD_HOTKEY.value:
                keys = p.get("keys", [])
                if not isinstance(keys, list) or not keys:
                    raise AssistantError("INVALID_PARAMS", "keys must be a non-empty list", 422)
                result = self.adapter.keyboard_hotkey([str(k) for k in keys])
            elif atype == ActionType.LAUNCH_APP.value:
                result = self.adapter.launch_application(str(p.get("app_id", "")), p.get("args"))
            elif atype == ActionType.FILE_LIST.value:
                files = [
                    {
                        "name": f.name,
                        "relative_path": str(f.relative_to(self.sandbox_root)),
                        "size_bytes": f.stat().st_size,
                    }
                    for f in sorted(self.sandbox_root.rglob("*"))
                    if f.is_file()
                ]
                result = {"sandbox_root": str(self.sandbox_root), "files": files, "count": len(files)}
            elif atype == ActionType.FILE_READ.value:
                target = self._resolve_sandbox_path(str(p.get("path", "")))
                if not target.is_file():
                    raise AssistantError("FILE_NOT_FOUND", f"Sandbox file '{p.get('path')}' not found", 404)
                result = {"path": str(p.get("path")), "content": target.read_text(encoding="utf-8")}
            elif atype == ActionType.FILE_WRITE.value:
                target = self._resolve_sandbox_path(str(p.get("path", "")))
                target.parent.mkdir(parents=True, exist_ok=True)
                content = str(p.get("content", ""))
                target.write_text(content, encoding="utf-8")
                result = {"path": str(p.get("path")), "bytes_written": len(content.encode("utf-8"))}
            elif atype == ActionType.FILE_DELETE.value:
                target = self._resolve_sandbox_path(str(p.get("path", "")))
                if not target.is_file():
                    raise AssistantError("FILE_NOT_FOUND", f"Sandbox file '{p.get('path')}' not found", 404)
                target.unlink()
                result = {"path": str(p.get("path")), "deleted": True}
            else:
                raise AssistantError("UNKNOWN_ACTION", f"Unsupported action_type '{atype}'", 422)

            dur_ms = round((time.perf_counter() - t0) * 1000, 2)
            updated = self.db.update_action(action_id, status=ActionStatus.EXECUTED.value, result=result, duration_ms=dur_ms)
            self.db.add_log(
                event_type="computer.action.executed",
                action_id=action_id,
                message=f"Executed '{atype}' in {dur_ms}ms.",
            )
            return updated  # type: ignore[return-value]
        except AssistantError as exc:
            dur_ms = round((time.perf_counter() - t0) * 1000, 2)
            self.db.update_action(action_id, status=ActionStatus.FAILED.value, error=exc.message, duration_ms=dur_ms)
            raise
        except Exception as exc:
            dur_ms = round((time.perf_counter() - t0) * 1000, 2)
            self.db.update_action(action_id, status=ActionStatus.FAILED.value, error=str(exc), duration_ms=dur_ms)
            self.db.add_log(
                event_type="computer.action.failed",
                level="ERROR",
                action_id=action_id,
                message=f"Action '{atype}' failed: {exc}",
            )
            raise AssistantError("ACTION_EXECUTION_FAILED", str(exc), 400) from exc

    # --- Approval Decisions ---
    def decide_approval(self, approval_id: str, approved: bool, decided_by: str = "operator", comment: str = "") -> Dict[str, Any]:
        apr = self.db.get_approval(approval_id)
        if not apr:
            raise AssistantError("APPROVAL_NOT_FOUND", f"Approval '{approval_id}' not found", 404)
        if apr["status"] != "pending":
            raise AssistantError("APPROVAL_ALREADY_DECIDED", f"Approval '{approval_id}' is already '{apr['status']}'", 409)
        if approved and self.estop_active:
            raise AssistantError("ESTOP_ACTIVE", "Cannot execute approved action while E-STOP is active.", 423)

        status = "approved" if approved else "rejected"
        decided = self.db.decide_approval(approval_id, status, decided_by, comment)
        action = self.db.get_action(apr["action_id"])
        assert action is not None
        if approved:
            executed = self._run_action_record(action)
            self.db.add_log(
                event_type="computer.approval.approved",
                action_id=action["action_id"],
                message=f"Approval '{approval_id}' approved by {decided_by}; action executed.",
            )
            return {"approval": decided, "action": executed}
        else:
            rejected = self.db.update_action(
                action["action_id"],
                status=ActionStatus.REJECTED.value,
                error=f"Rejected by {decided_by}: {comment or 'denied'}",
            )
            self.db.add_log(
                event_type="computer.approval.rejected",
                level="WARNING",
                action_id=action["action_id"],
                message=f"Approval '{approval_id}' rejected by {decided_by}.",
            )
            return {"approval": decided, "action": rejected}

    # --- Replay & Diagnostics ---
    def replay_actions(self, action_ids: List[str], dry_run: bool = True, requested_by: str = "operator") -> Dict[str, Any]:
        replayed: List[Dict[str, Any]] = []
        for aid in action_ids:
            orig = self.db.get_action(aid)
            if not orig:
                raise AssistantError("ACTION_NOT_FOUND", f"Original action '{aid}' not found for replay", 404)
            new_act = self.submit_action(
                action_type=orig["action_type"],
                params=orig["params"],
                dry_run=dry_run,
                requested_by=requested_by,
                reason=f"Replay of {aid}",
                replayed_from=aid,
            )
            replayed.append(new_act)
        return {"replayed_count": len(replayed), "dry_run": dry_run, "actions": replayed}

    def get_status(self) -> Dict[str, Any]:
        actions = self.db.list_actions(limit=500)
        by_status: Dict[str, int] = {}
        for a in actions:
            by_status[a["status"]] = by_status.get(a["status"], 0) + 1
        return {
            "adapter": self.adapter.get_state_snapshot(),
            "estop_active": self.estop_active,
            "estop_reason": self.estop_reason,
            "dry_run_mode": self.dry_run_mode,
            "policy": self.policy,
            "pending_approvals": len(self.db.list_approvals(status="pending")),
            "action_counts": by_status,
            "total_actions": len(actions),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }

    def get_diagnostics(self) -> Dict[str, Any]:
        actions = self.db.list_actions(limit=200)
        durations = [a["duration_ms"] for a in actions if a["duration_ms"] > 0]
        avg_ms = round(sum(durations) / len(durations), 2) if durations else 0.0
        return {
            "status": self.get_status(),
            "sandbox_root": str(self.sandbox_root),
            "average_action_duration_ms": avg_ms,
            "recent_failures": [a for a in actions if a["status"] in ("failed", "blocked_estop", "rejected")][:10],
            "recent_logs": self.db.list_logs(limit=40),
            "timestamp": utc_now_iso(),
        }
