"""
Agent Permission Manager for JARVIS OS Phase 5.
Enforces multi-profile permission governance (SAFE_AUTO, SUPERVISED_AUTO, MANUAL),
hard-deny security boundaries, project-scoped allow rules, and audit logging.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tools.agents.models import PermissionProfile, PermissionRequest, PermissionStatus

logger = logging.getLogger("JARVIS.PermissionManager")


class AgentPermissionManager:
    """Central authority governing AI agent actions, workspace permissions, and safety barriers."""

    # Hard-deny regex patterns that can NEVER be silently approved under ANY auto profile
    HARD_DENY_PATTERNS = [
        r"\brm\s+-(?:r|f|rf|fr)\s+[\/\~\*]",                               # Destructive recursive deletion
        r"\b(?:mkfs|fdisk|parted|sfdisk|gdisk)\b",                         # Disk formatting
        r"\bdd\s+if=\S+\s+of=\/dev\/\S+",                                  # dd to raw disks or devices
        r"\b(?:sudo\s+su|sudo\s+-i|sudo\s+bash|sudo\s+sh)\b",              # Unrestricted root shell
        r"\bchmod\s+777\s+[\/~]",                                          # System-wide permission destruction
        r"\b(?:cat|head|tail|less|grep)\b.*(?:\.env|\.ssh|id_rsa|\.aws)",  # Secret extraction
        r"\b(?:flash|esptool|avrdude|flashrom|firmware_flash)\b",          # Microcontroller flashing
        r"\b(?:robot_arm|robot_move|servo_set|enable_motors)\b",           # Robot physical actuators
        r"\b(?:iptables|ufw|nftables)\b.*(?:flush|disable|stop)",           # Firewall tampering
        r"\bgit\s+push\s+(?:--force|-f)?\s*(?:origin|upstream)?\s*(?:main|master|release)?\b", # Remote publishing
        r"\b(?:curl|wget)\s+https?://\S+\s*\|\s*(?:bash|sh)\b",            # Piping internet scripts into shell
    ]

    # Safe read-only commands
    SAFE_READ_COMMANDS = [
        r"^(?:ls|dir|pwd|whoami|date|uname|git\s+status|git\s+diff|git\s+log|pytest|python3?\s+-m\s+pytest|python3?\s+-m\s+py_compile)\b",
    ]

    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir or "/home/roshan/.gemini/antigravity/scratch/jarvis-os/data/agents")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "permissions.json"
        self.audit_log_file = self.config_dir / "permission_audit.jsonl"

        self.current_profile: PermissionProfile = PermissionProfile.SAFE_AUTO
        self.approved_workspaces: List[str] = [
            "/home/roshan/.gemini/antigravity/scratch/jarvis-os",
            "/home/roshan/UnityGameWorkspace",
            "/home/roshan/Downloads",
            "/tmp",
        ]
        self.project_scoped_rules: List[Dict[str, Any]] = []
        self._pending_requests: Dict[str, PermissionRequest] = {}

        self._load_config()

    def _load_config(self) -> None:
        """Load persistent permission settings from disk."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.current_profile = PermissionProfile(data.get("profile", PermissionProfile.SAFE_AUTO.value))
                self.approved_workspaces = data.get("approved_workspaces", self.approved_workspaces)
                self.project_scoped_rules = data.get("project_scoped_rules", [])
            except Exception as e:
                logger.warning("Failed to load permissions.json: %s", e)

    def _save_config(self) -> None:
        """Save permission configuration to disk."""
        try:
            data = {
                "profile": self.current_profile.value,
                "approved_workspaces": self.approved_workspaces,
                "project_scoped_rules": self.project_scoped_rules,
                "updated_at": time.time(),
            }
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning("Failed to save permissions.json: %s", e)

    def get_profile(self) -> PermissionProfile:
        return self.current_profile

    def set_profile(self, profile: PermissionProfile) -> Dict[str, Any]:
        """Switch active permission profile (SAFE_AUTO, SUPERVISED_AUTO, MANUAL)."""
        self.current_profile = profile
        self._save_config()
        logger.info("Agent permission profile switched to: %s", profile.value)
        return {"status": "ok", "profile": profile.value}

    def check_permission(
        self,
        agent_id: str,
        operation: str,
        target_path: Optional[str] = None,
        command: Optional[str] = None,
        working_dir: str = "/home/roshan",
        reason: str = "",
    ) -> Tuple[bool, PermissionRequest]:
        """Evaluate an agent operation against policy, hard-deny boundaries, and project rules."""
        req = PermissionRequest(
            agent_id=agent_id,
            operation=operation,
            target_path=target_path,
            command=command,
            working_dir=working_dir,
            reason=reason,
        )

        full_eval_str = f"{operation} {target_path or ''} {command or ''} {reason}".strip().lower()

        # 1. Hard-Deny Boundary Check (Highest Priority)
        for pattern in self.HARD_DENY_PATTERNS:
            if re.search(pattern, full_eval_str):
                req.risk_level = "CRITICAL"
                req.status = PermissionStatus.HARD_DENIED
                req.decision_reason = f"Operation violated hard-deny security rule: {pattern}"
                req.decided_at = time.time()
                self._record_audit(req)
                logger.warning("HARD-DENIED operation from %s: %s", agent_id, req.decision_reason)
                return False, req

        # 2. Workspace Boundary Check
        is_in_approved_workspace = False
        eval_path = target_path or working_dir
        if eval_path:
            abs_eval = os.path.abspath(eval_path)
            for ws in self.approved_workspaces:
                if abs_eval == ws or abs_eval.startswith(ws.rstrip("/") + "/"):
                    is_in_approved_workspace = True
                    break

        # 3. Project-scoped allow rules
        for rule in self.project_scoped_rules:
            if rule.get("agent_id") in (agent_id, "*"):
                if rule.get("operation") in (operation, "*"):
                    rule_path = rule.get("path")
                    if not rule_path or (target_path and target_path.startswith(rule_path)):
                        req.status = PermissionStatus.AUTO_APPROVED
                        req.decision_reason = f"Approved by project rule: {rule.get('name', 'custom rule')}"
                        req.decided_at = time.time()
                        self._record_audit(req)
                        return True, req

        # 4. Profile Evaluation
        if self.current_profile == PermissionProfile.SAFE_AUTO:
            # Safe read-only or workspace test/inspection is auto-allowed
            if operation in ("read_file", "file_read", "list_dir", "git_status", "git_diff", "run_tests", "search_code"):
                if is_in_approved_workspace or operation in ("list_dir", "git_status"):
                    req.status = PermissionStatus.AUTO_APPROVED
                    req.decision_reason = "Safe read operation auto-approved in SAFE_AUTO mode."
                    req.decided_at = time.time()
                    self._record_audit(req)
                    return True, req

            # Safe in-workspace file edits (targeted patches after backup)
            if operation in ("modify_file", "file_write", "write_file", "apply_patch", "create_test") and is_in_approved_workspace:
                req.status = PermissionStatus.AUTO_APPROVED
                req.decision_reason = "Workspace code modification auto-approved with pre-backup in SAFE_AUTO mode."
                req.decided_at = time.time()
                self._record_audit(req)
                return True, req

            # Safe read commands in shell
            if command and any(re.search(pat, command.strip()) for pat in self.SAFE_READ_COMMANDS):
                req.status = PermissionStatus.AUTO_APPROVED
                req.decision_reason = "Safe command auto-approved in SAFE_AUTO mode."
                req.decided_at = time.time()
                self._record_audit(req)
                return True, req

        elif self.current_profile == PermissionProfile.SUPERVISED_AUTO:
            # Auto-allow safe reads
            if operation in ("read_file", "file_read", "list_dir", "git_status", "run_tests"):
                req.status = PermissionStatus.AUTO_APPROVED
                req.decision_reason = "Safe operation auto-approved in SUPERVISED_AUTO mode."
                req.decided_at = time.time()
                self._record_audit(req)
                return True, req

        # If not auto-approved, stage as PENDING for user approval
        req.risk_level = "HIGH" if not is_in_approved_workspace else "MEDIUM"
        req.status = PermissionStatus.PENDING
        req.decision_reason = "Operation requires interactive user confirmation."
        self._pending_requests[req.request_id] = req
        self._record_audit(req)
        logger.info("Staged pending permission request %s for %s (%s)", req.request_id, agent_id, operation)
        return False, req

    def approve_request(self, request_id: str, create_similar_rule: bool = False) -> Dict[str, Any]:
        """Approve a pending permission request (Approve Once or Approve Similar)."""
        req = self._pending_requests.get(request_id)
        if not req:
            return {"status": "error", "message": f"Request {request_id} not found"}

        req.status = PermissionStatus.APPROVED
        req.decision_reason = "Manually approved by user."
        req.decided_at = time.time()
        self._record_audit(req)
        del self._pending_requests[request_id]

        rule_created = None
        if create_similar_rule and req.target_path:
            rule_dir = str(Path(req.target_path).parent)
            new_rule = {
                "name": f"Allow {req.operation} in {rule_dir}",
                "agent_id": req.agent_id,
                "operation": req.operation,
                "path": rule_dir,
                "created_at": time.time(),
            }
            self.project_scoped_rules.append(new_rule)
            self._save_config()
            rule_created = new_rule

        return {
            "status": "ok",
            "request_id": request_id,
            "decision": "APPROVED",
            "similar_rule_created": rule_created,
        }

    def deny_request(self, request_id: str, reason: str = "Denied by user") -> Dict[str, Any]:
        """Deny a pending permission request."""
        req = self._pending_requests.get(request_id)
        if not req:
            return {"status": "error", "message": f"Request {request_id} not found"}

        req.status = PermissionStatus.DENIED
        req.decision_reason = reason
        req.decided_at = time.time()
        self._record_audit(req)
        del self._pending_requests[request_id]

        return {"status": "ok", "request_id": request_id, "decision": "DENIED"}

    def get_pending_requests(self) -> List[Dict[str, Any]]:
        """Return all permission requests awaiting decision."""
        return [r.to_dict() for r in self._pending_requests.values()]

    def get_audit_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent permission decisions from audit log."""
        if not self.audit_log_file.exists():
            return []
        records = []
        try:
            with open(self.audit_log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
        except Exception as e:
            logger.warning("Failed to read audit log: %s", e)
        return records[-limit:]

    def _record_audit(self, req: PermissionRequest) -> None:
        """Append permission decision to audit log with secrets redacted."""
        clean_dict = req.to_dict()
        # Redact any accidental tokens or passwords
        if clean_dict.get("command"):
            clean_dict["command"] = re.sub(r"(?:token|key|password|secret)=[^\s&]+", "REDACTED", clean_dict["command"], flags=re.I)
        try:
            with open(self.audit_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(clean_dict) + "\n")
        except Exception:
            pass


permission_manager = AgentPermissionManager()
