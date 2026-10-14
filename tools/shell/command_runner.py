"""
JARVIS Secure Command Runner
Never uses shell=True. Never concatenates user input into shell strings.
Uses explicit allowlist of permitted commands.
"""
import subprocess
import logging
import shutil
import time
from typing import Dict, Any, List, Optional

logger = logging.getLogger("JARVIS.Tools.Shell")

# Commands that JARVIS is permitted to execute directly.
# Anything not in this list is rejected before subprocess.run is called.
ALLOWED_COMMANDS: Dict[str, dict] = {
    "systemctl":  {"description": "Manage systemd services", "risk": 2},
    "git":        {"description": "Git version control",     "risk": 1},
    "python3":    {"description": "Run Python scripts",      "risk": 1},
    "pip":        {"description": "Python package manager",  "risk": 2},
    "pip3":       {"description": "Python package manager",  "risk": 2},
    "ls":         {"description": "List directory",          "risk": 0},
    "cat":        {"description": "Print file content",      "risk": 0},
    "grep":       {"description": "Search text",             "risk": 0},
    "find":       {"description": "Find files",              "risk": 0},
    "df":         {"description": "Disk usage",              "risk": 0},
    "free":       {"description": "Memory usage",            "risk": 0},
    "ps":         {"description": "Process list",            "risk": 0},
    "journalctl": {"description": "System logs",             "risk": 0},
    "curl":       {"description": "HTTP requests",           "risk": 1},
    "ping":       {"description": "Network ping",            "risk": 0},
    "uname":      {"description": "Kernel info",             "risk": 0},
    "i2cdetect":  {"description": "I2C device scan",         "risk": 0},
    "arecord":    {"description": "Audio recording",         "risk": 1},
    "aplay":      {"description": "Audio playback",          "risk": 1},
    "espeak":     {"description": "Text to speech",          "risk": 1},
    "pytest":     {"description": "Run tests",               "risk": 1},
    "node":       {"description": "Node.js runtime",         "risk": 1},
    "npm":        {"description": "Node package manager",    "risk": 2},
    "make":       {"description": "Build tool",              "risk": 1},
    "tar":        {"description": "Archive tool",            "risk": 1},
    "cp":         {"description": "Copy files",              "risk": 1},
    "mv":         {"description": "Move files",              "risk": 2},
    "mkdir":      {"description": "Create directory",        "risk": 1},
    "chmod":      {"description": "Change permissions",      "risk": 2},
    "chown":      {"description": "Change owner",            "risk": 3},
    "apt-get":    {"description": "Package manager",         "risk": 3},
    "raspi-config": {"description": "Pi configuration",     "risk": 4},
}

DENIED_ARGS = [
    "rm -rf", "--force", "format", "mkfs", "dd if=", ":(){ :|:& };:",
    "/dev/sda", "chmod 777 /", "chown root", "/etc/shadow", "/etc/passwd",
]


class SecureCommandRunner:
    """
    Execute shell commands safely.
    - No shell=True ever.
    - Explicit allowlist.
    - Arg-level denylist for known dangerous patterns.
    - Timeout enforced.
    - Returns structured result, never raises to caller.
    """

    def __init__(self, max_timeout: int = 60) -> None:
        self.max_timeout = max_timeout

    def is_allowed(self, command: str) -> bool:
        return command in ALLOWED_COMMANDS

    def _check_args(self, args: List[str]) -> Optional[str]:
        combined = " ".join(args).lower()
        for denied in DENIED_ARGS:
            if denied.lower() in combined:
                return f"Denied argument pattern detected: '{denied}'"
        return None

    def execute(self, command: str, args: Optional[List[str]] = None,
                timeout: int = 30, cwd: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute command with args safely.
        Returns: {success, returncode, stdout, stderr, duration_ms, error}
        """
        args = args or []
        timeout = min(timeout, self.max_timeout)

        if not self.is_allowed(command):
            msg = f"Command '{command}' is not in ALLOWED_COMMANDS."
            logger.warning(msg)
            return {"success": False, "returncode": 126,
                    "stdout": "", "stderr": msg, "duration_ms": 0, "error": msg}

        deny_reason = self._check_args(args)
        if deny_reason:
            logger.warning(deny_reason)
            return {"success": False, "returncode": -1,
                    "stdout": "", "stderr": deny_reason,
                    "duration_ms": 0, "error": deny_reason}

        # Resolve full path to binary (prevents path injection)
        binary = shutil.which(command)
        if not binary:
            msg = f"Command '{command}' not found on PATH."
            logger.error(msg)
            return {"success": False, "returncode": 126,
                    "stdout": "", "stderr": msg, "duration_ms": 0, "error": msg}

        cmd_list = [binary] + args
        start = time.monotonic()
        try:
            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                shell=False,  # Never True
            )
            duration_ms = (time.monotonic() - start) * 1000
            logger.debug(f"[CMD] {command} {args} → rc={result.returncode} ({duration_ms:.0f}ms)")
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout[:10000],   # Cap output size
                "stderr": result.stderr[:5000],
                "duration_ms": round(duration_ms, 1),
                "error": None,
            }
        except subprocess.TimeoutExpired:
            msg = f"Command '{command}' timed out after {timeout}s"
            logger.warning(msg)
            return {"success": False, "returncode": -1,
                    "stdout": "", "stderr": msg, "duration_ms": timeout * 1000, "error": msg}
        except Exception as e:
            msg = f"Command execution error: {e}"
            logger.error(msg)
            return {"success": False, "returncode": 126,
                    "stdout": "", "stderr": msg, "duration_ms": 0, "error": msg}

    def execute_command(self, command: str, args=None,
                        timeout: int = 30, cwd=None) -> dict:
        """Alias for execute() for backwards-compatibility."""
        return self.execute(command, args or [], timeout, cwd)

# Module-level singleton
command_runner = SecureCommandRunner()
