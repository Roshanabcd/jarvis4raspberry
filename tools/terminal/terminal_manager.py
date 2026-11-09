"""
JARVIS Real Terminal Execution Engine
Provides interactive and persistent terminal sessions, per-session directory
tracking, real stdout/stderr/exit-code capture, process tracking, and a security
confirmation gate for privileged or destructive operations.
"""
from __future__ import annotations

import logging
import os
import re
import shlex
import subprocess
import time
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger("JARVIS-TERMINAL-ENGINE")

# Patterns requiring explicit confirmation before execution
DESTRUCTIVE_PATTERNS = [
    r"\bsudo\b",
    r"\brm\s+-(?:r|f|rf|fr)\b",
    r"\brmdir\b",
    r"\bmkfs\b",
    r"\bfdisk\b",
    r"\bparted\b",
    r"\bdd\s+if=",
    r"\bchmod\s+-[rR]\b",
    r"\bchown\s+-[rR]\b",
    r"\b(?:apt|apt-get|dpkg)\s+(?:install|remove|purge|upgrade)\b",
    r"\bsystemctl\s+(?:stop|disable|mask|restart)\b",
    r"\biptables\b",
    r"\bufw\b",
    r"\bkill\s+-9\b",
    r"\bkillall\b",
    r"\bpkill\b",
    r"\|\s*(?:bash|sh|zsh)\b",
]


class TerminalSession:
    """Represents a persistent interactive terminal session with directory tracking."""

    def __init__(self, session_id: str, initial_dir: Optional[str] = None) -> None:
        self.session_id = session_id
        home = os.path.expanduser("~")
        self.cwd = os.path.realpath(initial_dir) if initial_dir and os.path.isdir(initial_dir) else home
        self.history: List[Dict[str, Any]] = []
        self.env: Dict[str, str] = os.environ.copy()
        self.created_at = time.time()
        self.last_active = time.time()

    def change_directory(self, target: str) -> Dict[str, Any]:
        """Safely change session working directory."""
        clean_t = target.strip().strip("'\"")
        exp = os.path.expanduser(clean_t)
        if not os.path.isabs(exp):
            candidate = os.path.realpath(os.path.join(self.cwd, exp))
        else:
            candidate = os.path.realpath(exp)

        if os.path.isdir(candidate):
            self.cwd = candidate
            self.last_active = time.time()
            return {"success": True, "cwd": self.cwd, "message": f"Changed directory to {self.cwd}"}
        return {"success": False, "cwd": self.cwd, "error": f"Directory '{target}' does not exist."}


class TerminalExecutionEngine:
    """Central manager for persistent terminal sessions and safe command execution."""

    def __init__(self) -> None:
        self._sessions: Dict[str, TerminalSession] = {}
        self._confirmation_tokens: Dict[str, Dict[str, Any]] = {}
        # Ensure default session exists
        self.get_or_create_session("default")

    def get_or_create_session(self, session_id: Optional[str] = None) -> TerminalSession:
        sid = session_id or "default"
        if sid not in self._sessions:
            self._sessions[sid] = TerminalSession(sid)
        return self._sessions[sid]

    def list_sessions(self) -> List[Dict[str, Any]]:
        return [
            {
                "session_id": s.session_id,
                "cwd": s.cwd,
                "commands_run": len(s.history),
                "created_at": s.created_at,
                "last_active": s.last_active,
            }
            for s in self._sessions.values()
        ]

    def is_destructive(self, command: str) -> Optional[str]:
        """Check if command matches destructive or security-sensitive patterns."""
        cmd_lower = command.lower()
        for pat in DESTRUCTIVE_PATTERNS:
            if re.search(pat, cmd_lower):
                return pat
        return None

    def execute_command(
        self,
        command: str,
        session_id: Optional[str] = None,
        confirm: bool = False,
        confirmation_token: Optional[str] = None,
        timeout: int = 45,
    ) -> Dict[str, Any]:
        """Execute command in real terminal with session directory tracking and real output capture."""
        session = self.get_or_create_session(session_id)
        cmd_str = command.strip()
        t_start = time.time()

        if not cmd_str:
            return {
                "success": False,
                "status": "empty_command",
                "command": "",
                "exit_code": 0,
                "stdout": "",
                "stderr": "",
                "cwd": session.cwd,
                "duration_ms": 0,
            }

        # 1. Check for directory change command (`cd <dir>`)
        cd_match = re.match(r"^cd(?:\s+(.*))?$", cmd_str)
        if cd_match:
            target_dir = cd_match.group(1) or os.path.expanduser("~")
            cd_res = session.change_directory(target_dir)
            dur_ms = int((time.time() - t_start) * 1000)
            record = {
                "command": cmd_str,
                "cwd": session.cwd,
                "exit_code": 0 if cd_res["success"] else 1,
                "stdout": cd_res.get("message", "") if cd_res["success"] else "",
                "stderr": cd_res.get("error", "") if not cd_res["success"] else "",
                "duration_ms": dur_ms,
                "timestamp": time.time(),
                "status": "SUCCESS" if cd_res["success"] else "FAILED",
            }
            session.history.append(record)
            return record

        # 2. Security Confirmation Gate
        matched_pat = self.is_destructive(cmd_str)
        if matched_pat and not confirm:
            # Check if valid confirmation token was provided
            if confirmation_token and confirmation_token in self._confirmation_tokens:
                token_data = self._confirmation_tokens.pop(confirmation_token)
                if token_data.get("command") != cmd_str:
                    return {
                        "requires_confirmation": True,
                        "error": "Confirmation token does not match command.",
                        "command": cmd_str,
                    }
            else:
                token = f"tok_{uuid.uuid4().hex[:12]}"
                self._confirmation_tokens[token] = {"command": cmd_str, "time": time.time()}
                return {
                    "requires_confirmation": True,
                    "status": "CONFIRMATION_REQUIRED",
                    "command": cmd_str,
                    "cwd": session.cwd,
                    "reason": f"Command contains sensitive or destructive pattern: '{matched_pat}'.",
                    "confirmation_token": token,
                    "message": f"⚠️ Action Required: Executing '{cmd_str}' requires explicit user confirmation. Re-run with confirmation_token or confirm=True to proceed.",
                    "exit_code": None,
                    "stdout": "",
                    "stderr": "",
                }

        # 3. Real Subprocess Execution in Session CWD
        env = session.env.copy()
        if "DISPLAY" not in env:
            env["DISPLAY"] = ":0"

        try:
            # Execute with bash so pipes, subshells, and complex commands work naturally
            proc = subprocess.run(
                ["/bin/bash", "-c", cmd_str],
                cwd=session.cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
            )
            dur_ms = int((time.time() - t_start) * 1000)
            status = "SUCCESS" if proc.returncode == 0 else "FAILED"
            record = {
                "command": cmd_str,
                "cwd": session.cwd,
                "exit_code": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "duration_ms": dur_ms,
                "timestamp": time.time(),
                "status": status,
            }
            session.last_active = time.time()
            session.history.append(record)
            return record

        except subprocess.TimeoutExpired:
            dur_ms = timeout * 1000
            record = {
                "command": cmd_str,
                "cwd": session.cwd,
                "exit_code": 124,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds.",
                "duration_ms": dur_ms,
                "timestamp": time.time(),
                "status": "TIMEOUT",
            }
            session.history.append(record)
            return record
        except Exception as e:
            dur_ms = int((time.time() - t_start) * 1000)
            record = {
                "command": cmd_str,
                "cwd": session.cwd,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "duration_ms": dur_ms,
                "timestamp": time.time(),
                "status": "ERROR",
            }
            session.history.append(record)
            return record

    def get_history(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        session = self.get_or_create_session(session_id)
        return session.history


terminal_engine = TerminalExecutionEngine()
