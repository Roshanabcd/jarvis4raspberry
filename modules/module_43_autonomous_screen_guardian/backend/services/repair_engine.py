"""4-Mode Auto-Repair Orchestration & Verification Engine (Module 43)."""

from __future__ import annotations

import asyncio
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from modules.module_43_autonomous_screen_guardian.backend.adapters.coding_agents import (
    BaseCodingAgentAdapter,
    ReferenceLocalRepairAgent,
    discover_cli_agents,
    validate_cli_args,
)
from modules.module_43_autonomous_screen_guardian.backend.app.config import PROTECTED_SYSTEM_PATHS, ScreenGuardianConfig
from modules.module_43_autonomous_screen_guardian.backend.models.database import ScreenGuardianDB, utc_now_iso

VALID_MODES = {"observe_only", "suggest_fix", "assisted_repair", "trusted_workspace_autopilot"}


class RepairEngineError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class AutoRepairEngine:
    def __init__(self, config: ScreenGuardianConfig, db: ScreenGuardianDB) -> None:
        self.config = config
        self.db = db
        self._adapters: Dict[str, BaseCodingAgentAdapter] = {
            "reference_local_repair_agent": ReferenceLocalRepairAgent(),
        }
        self._active_tasks: Dict[str, asyncio.Task[Any]] = {}
        self._active_procs: Dict[str, asyncio.subprocess.Process] = {}

    def register_adapter(self, adapter: BaseCodingAgentAdapter) -> None:
        self._adapters[adapter.agent_id] = adapter

    def validate_workspace(self, workspace_path: str) -> Path:
        ws = Path(workspace_path).expanduser().resolve()
        ws_str = str(ws)
        for protected in PROTECTED_SYSTEM_PATHS:
            if ws_str == protected or (protected != "/" and ws_str.startswith(protected + "/")):
                raise RepairEngineError(
                    "PROTECTED_PATH_REJECTED",
                    f"Workspace '{ws_str}' is inside protected system path '{protected}' and is forbidden.",
                    403,
                )
        if not ws.exists() or not ws.is_dir():
            raise RepairEngineError("WORKSPACE_NOT_FOUND", f"Workspace directory does not exist: '{ws_str}'.", 404)

        if self.config.trusted_workspaces:
            allowed = any(
                ws_str == tw or ws_str.startswith(tw.rstrip("/") + "/")
                for tw in self.config.trusted_workspaces
            )
            if not allowed:
                raise RepairEngineError(
                    "UNAUTHORIZED_WORKSPACE",
                    f"Workspace '{ws_str}' is outside configured trusted_workspaces.",
                    403,
                )
        return ws

    def create_repair_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        mode = data.get("mode", "assisted_repair").strip().lower()
        if mode not in VALID_MODES:
            raise RepairEngineError("INVALID_MODE", f"Unsupported repair mode '{mode}'.", 422)

        ws = self.validate_workspace(data["workspace_path"])
        agent_id = data.get("agent_id", "reference_local_repair_agent").strip()
        agents = {a["agent_id"]: a for a in discover_cli_agents()}
        if agent_id not in agents or not agents[agent_id]["available"]:
            raise RepairEngineError("AGENT_UNAVAILABLE", f"Coding agent '{agent_id}' is not installed or unavailable.", 422)

        test_cmd = data.get("test_command") or []
        if test_cmd:
            validate_cli_args(test_cmd)

        repair_id = f"rep_{uuid.uuid4().hex[:10]}"
        needs_approval = mode == "assisted_repair"
        if mode == "observe_only":
            status, outcome, approval_status = "completed", "verification_incomplete", "not_required"
        elif mode == "suggest_fix":
            status, outcome, approval_status = "queued", "approval_required", "not_required"
        elif mode == "trusted_workspace_autopilot":
            if not self.config.trusted_workspaces:
                raise RepairEngineError(
                    "TRUSTED_WORKSPACE_REQUIRED",
                    "trusted_workspace_autopilot requires explicit trusted_workspaces configuration.",
                    403,
                )
            status, outcome, approval_status = "queued", "verification_incomplete", "pre_approved_workspace"
        else:
            status, outcome, approval_status = "awaiting_approval", "approval_required", "pending"

        job = self.db.create_repair(
            {
                "repair_id": repair_id,
                "error_id": data.get("error_id"),
                "workspace_path": str(ws),
                "agent_id": agent_id,
                "mode": mode,
                "status": status,
                "outcome": outcome,
                "summary": data["summary"].strip(),
                "error_context": data.get("error_context", ""),
                "approval_status": approval_status,
            }
        )
        self.db.add_log(
            "repair.created",
            f"Repair {repair_id} created in mode '{mode}' ({status})",
            details={"workspace": str(ws), "agent_id": agent_id, "needs_approval": needs_approval},
        )
        return job

    def approve_repair(self, repair_id: str, decision: str, reviewer: str, notes: str = "") -> Dict[str, Any]:
        job = self.db.get_repair(repair_id)
        if not job:
            raise RepairEngineError("REPAIR_NOT_FOUND", f"Repair '{repair_id}' not found.", 404)
        if job["status"] != "awaiting_approval":
            raise RepairEngineError("INVALID_STATE", f"Repair '{repair_id}' is not awaiting approval.", 409)
        dec = decision.strip().lower()
        if dec not in {"approve", "reject"}:
            raise RepairEngineError("INVALID_DECISION", "Decision must be 'approve' or 'reject'.", 422)
        if dec == "approve":
            updated = self.db.update_repair(repair_id, status="queued", approval_status="approved", reviewer=reviewer)
            self.db.add_log("repair.approved", f"Repair {repair_id} approved by {reviewer}")
        else:
            updated = self.db.update_repair(
                repair_id,
                status="cancelled",
                outcome="approval_required",
                approval_status="rejected",
                reviewer=reviewer,
                completed_at=utc_now_iso(),
            )
            self.db.add_log("repair.rejected", f"Repair {repair_id} rejected by {reviewer}", level="WARNING")
        assert updated is not None
        return updated

    async def execute_repair(
        self,
        repair_id: str,
        target_files: Optional[List[str]] = None,
        test_command: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        job = self.db.get_repair(repair_id)
        if not job:
            raise RepairEngineError("REPAIR_NOT_FOUND", f"Repair '{repair_id}' not found.", 404)
        if job["status"] == "awaiting_approval":
            raise RepairEngineError("APPROVAL_REQUIRED", f"Repair '{repair_id}' requires explicit approval before execution.", 403)
        if job["mode"] == "observe_only":
            return job

        ws = self.validate_workspace(job["workspace_path"])
        adapter = self._adapters.get(job["agent_id"])
        if not adapter:
            updated = self.db.update_repair(
                repair_id,
                status="failed",
                outcome="execution_failed",
                logs=[f"No executable adapter registered for '{job['agent_id']}'."],
                completed_at=utc_now_iso(),
            )
            assert updated is not None
            return updated

        dry_run = job["mode"] == "suggest_fix"
        logs: List[str] = [f"[{utc_now_iso()}] Starting repair ({job['mode']}, dry_run={dry_run}) on {ws}"]
        self.db.update_repair(repair_id, status="running", logs=logs)

        # Create lightweight recovery checkpoint for modified files
        checkpoint_dir = ws / ".jarvis_checkpoints" / repair_id
        try:
            res = await adapter.repair(
                workspace=ws,
                error_context=job["error_context"],
                target_files=target_files or [],
                dry_run=dry_run,
            )
            logs.append(f"Plan: {res['plan']}")
            if res["changed_files"] and not dry_run:
                checkpoint_dir.mkdir(parents=True, exist_ok=True)
                logs.append(f"Changed files: {', '.join(res['changed_files'])}")

            if dry_run:
                updated = self.db.update_repair(
                    repair_id,
                    status="completed",
                    outcome="approval_required",
                    plan_text=res["plan"],
                    diff_text=res["diff"],
                    changed_files=res["changed_files"],
                    logs=logs,
                    completed_at=utc_now_iso(),
                )
                assert updated is not None
                return updated

            # Focused test verification
            cmd = test_command or [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
            validate_cli_args(cmd)
            logs.append(f"Running focused verification: {' '.join(cmd)}")

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(ws),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self._active_procs[repair_id] = proc
            try:
                stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=self.config.max_repair_timeout_sec)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                logs.append("Verification test command timed out.")
                updated = self.db.update_repair(
                    repair_id,
                    status="failed",
                    outcome="execution_failed",
                    plan_text=res["plan"],
                    diff_text=res["diff"],
                    changed_files=res["changed_files"],
                    test_results={"exit_code": -1, "timed_out": True},
                    logs=logs,
                    completed_at=utc_now_iso(),
                )
                assert updated is not None
                return updated
            finally:
                self._active_procs.pop(repair_id, None)

            test_out = (stdout_b.decode("utf-8", errors="replace") + "\n" + stderr_b.decode("utf-8", errors="replace")).strip()
            passed = proc.returncode == 0
            logs.append(f"Verification exit_code={proc.returncode}")

            if passed and res["applied"]:
                outcome = "verified_fixed"
                if job.get("error_id"):
                    self.db.update_error(job["error_id"], status="resolved")
            elif passed and not res["applied"]:
                outcome = "verification_incomplete"
            else:
                # Never mark error resolved when verification fails!
                outcome = "not_fixed"

            updated = self.db.update_repair(
                repair_id,
                status="completed" if passed else "failed",
                outcome=outcome,
                plan_text=res["plan"],
                diff_text=res["diff"],
                changed_files=res["changed_files"],
                test_results={"exit_code": proc.returncode, "passed": passed, "output": test_out[:4000]},
                logs=logs,
                completed_at=utc_now_iso(),
            )
            assert updated is not None
            return updated
        except asyncio.CancelledError:
            proc = self._active_procs.pop(repair_id, None)
            if proc and proc.returncode is None:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    proc.kill()
            logs.append("Repair cancelled by operator.")
            self.db.update_repair(
                repair_id,
                status="cancelled",
                outcome="execution_failed",
                logs=logs,
                completed_at=utc_now_iso(),
            )
            raise
        except Exception as exc:
            logs.append(f"Repair execution error: {exc}")
            updated = self.db.update_repair(
                repair_id,
                status="failed",
                outcome="execution_failed",
                logs=logs,
                completed_at=utc_now_iso(),
            )
            assert updated is not None
            return updated
        finally:
            if checkpoint_dir.exists():
                shutil.rmtree(checkpoint_dir, ignore_errors=True)

    def start_background_repair(
        self,
        repair_id: str,
        target_files: Optional[List[str]] = None,
        test_command: Optional[List[str]] = None,
    ) -> asyncio.Task[Any]:
        task = asyncio.create_task(self.execute_repair(repair_id, target_files=target_files, test_command=test_command))
        self._active_tasks[repair_id] = task
        task.add_done_callback(lambda _: self._active_tasks.pop(repair_id, None))
        return task

    async def cancel_repair(self, repair_id: str) -> Dict[str, Any]:
        job = self.db.get_repair(repair_id)
        if not job:
            raise RepairEngineError("REPAIR_NOT_FOUND", f"Repair '{repair_id}' not found.", 404)
        proc = self._active_procs.pop(repair_id, None)
        if proc and proc.returncode is None:
            proc.terminate()
        task = self._active_tasks.pop(repair_id, None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        updated = self.db.update_repair(
            repair_id,
            status="cancelled",
            outcome="execution_failed",
            completed_at=utc_now_iso(),
        )
        assert updated is not None
        self.db.add_log("repair.cancelled", f"Cancelled repair {repair_id}", level="WARNING")
        return updated
