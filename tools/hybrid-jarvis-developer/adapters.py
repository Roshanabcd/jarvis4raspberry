"""
Real and Simulated Execution Adapters for Hybrid JARVIS Multi-Agent Orchestrator.
Supports Google Antigravity (agy), OpenAI Codex (codex), GitHub Copilot (copilot),
and deterministic simulation for testing.
"""
from dataclasses import dataclass
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
from typing import Any, Dict, List, Optional
from .models import Task

logger = logging.getLogger("JARVIS.Developer.Adapters")

_SECRET_PATTERN = re.compile(r"(?i)(api[_-]?key|token|password|secret)(\s*[=:]\s*)[^\s,;]+")

def redact(value: Any) -> str:
    return _SECRET_PATTERN.sub(r"\1\2[REDACTED]", str(value))


class RateLimitError(RuntimeError):
    """Raised when an agent CLI hits API quota or rate limits."""
    pass


class SimulatedWorktreeAgent:
    """Deterministic simulated agent that creates synthetic diffs when a worktree is attached."""
    integration_type = "simulated"
    detail = "Deterministic simulated mock agent for CI/CD"

    def __init__(self, response: str = "Simulated execution verified cleanly.", fail_times: int = 0):
        self.response = response
        self.fail_times = fail_times
        self.calls = 0

    def is_available(self) -> bool:
        return True

    def execute(self, task: Task) -> Dict[str, Any]:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError(f"simulated failure attempt {self.calls}")

        modified_files = []
        if getattr(task, "worktree", None) and Path(task.worktree).exists():
            sim_file = Path(task.worktree) / f"SIMULATED_{task.task_id[:8]}.txt"
            sim_file.write_text(f"Simulated execution for task {task.task_id}\nPrompt: {task.prompt}\n")
            modified_files.append(sim_file.name)

        return {
            "status": "ok",
            "agent": "simulated",
            "message": self.response,
            "worktree": getattr(task, "worktree", None),
            "modified_files": modified_files,
        }

    def cancel(self):
        pass


class AntigravityCliAdapter:
    """
    Real non-interactive execution adapter using Google Antigravity CLI (agy).
    Enforces terminal sandboxing (--sandbox) by default.
    """
    integration_type = "real_cli"
    detail = "Google Antigravity CLI (agy v1.5.10)"

    def __init__(self, executable: Optional[str] = None, sandboxed: bool = True, effort: str = "medium"):
        self.executable = executable or shutil.which("agy") or "/home/roshan/.local/bin/agy"
        self.sandboxed = sandboxed
        self.effort = effort
        self._active_procs: Dict[str, subprocess.Popen] = {}
        self._lock = threading.Lock()

    def is_available(self) -> bool:
        return bool(self.executable and Path(self.executable).is_file() and os.access(self.executable, os.X_OK))

    def execute(self, task: Task) -> Dict[str, Any]:
        if not self.is_available():
            raise RuntimeError(f"Antigravity CLI executable not found at {self.executable}")

        work_dir = task.worktree if (getattr(task, "worktree", None) and Path(task.worktree).exists()) else str(Path.cwd())
        
        cmd = [self.executable, "-p", task.prompt]
        if self.sandboxed:
            cmd.append("--sandbox")
        if self.effort:
            cmd.extend(["--effort", self.effort])

        logger.info("Executing Antigravity task %s in %s (sandboxed: %s)", task.task_id, work_dir, self.sandboxed)
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=work_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            with self._lock:
                self._active_procs[task.task_id] = proc

            try:
                stdout, stderr = proc.communicate(timeout=task.timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                raise TimeoutError(f"Antigravity execution exceeded timeout of {task.timeout}s")
            finally:
                with self._lock:
                    self._active_procs.pop(task.task_id, None)

            if proc.returncode != 0:
                err_msg = stderr.strip() or stdout.strip() or f"Antigravity exited with code {proc.returncode}"
                raise RuntimeError(err_msg[:400])

            modified_files = []
            if getattr(task, "worktree", None) and Path(task.worktree).exists():
                st = subprocess.run(
                    ["git", "-C", task.worktree, "status", "--porcelain"],
                    capture_output=True, text=True
                ).stdout
                modified_files = [line.strip().split(maxsplit=1)[-1] for line in st.splitlines() if line.strip()]

            return {
                "status": "ok",
                "agent": "antigravity",
                "version": "1.5.10",
                "task_id": task.task_id,
                "worktree": getattr(task, "worktree", None),
                "output": redact(stdout.strip()[:2000]),
                "modified_files": modified_files,
                "sandboxed": self.sandboxed,
            }
        except Exception as exc:
            logger.error("Antigravity execution error for task %s: %s", task.task_id, exc)
            raise

    def cancel(self, task_id: Optional[str] = None):
        with self._lock:
            if task_id:
                proc = self._active_procs.get(task_id)
                if proc:
                    try:
                        proc.kill()
                    except Exception:
                        pass
            else:
                for proc in self._active_procs.values():
                    try:
                        proc.kill()
                    except Exception:
                        pass


class CopilotCliAdapter:
    """
    Real non-interactive execution adapter using GitHub Copilot CLI (copilot).
    Uses granular sandboxed tools (--allow-tool=write, --add-dir) rather than --allow-all.
    """
    integration_type = "real_cli"
    detail = "GitHub Copilot CLI (v1.0.112 · Copilot Fusion / GPT-5.6)"

    def __init__(self, executable: Optional[str] = None, sandboxed: bool = True):
        self.executable = executable or shutil.which("copilot") or "/home/roshan/.local/bin/copilot"
        self.sandboxed = sandboxed
        self._active_procs: Dict[str, subprocess.Popen] = {}
        self._lock = threading.Lock()

    def is_available(self) -> bool:
        return bool(self.executable and Path(self.executable).is_file() and os.access(self.executable, os.X_OK))

    def execute(self, task: Task) -> Dict[str, Any]:
        if not self.is_available():
            raise RuntimeError(f"GitHub Copilot CLI executable not found at {self.executable}")

        work_dir = task.worktree if (getattr(task, "worktree", None) and Path(task.worktree).exists()) else str(Path.cwd())
        
        cmd = [self.executable, "-p", task.prompt]
        if self.sandboxed and getattr(task, "worktree", None):
            cmd.extend([
                "--allow-tool=write",
                "--allow-tool=shell(git:*)",
                f"--add-dir={task.worktree}",
            ])

        logger.info("Executing Copilot task %s in %s (sandboxed: %s)", task.task_id, work_dir, self.sandboxed)
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=work_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            with self._lock:
                self._active_procs[task.task_id] = proc

            try:
                stdout, stderr = proc.communicate(timeout=task.timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                raise TimeoutError(f"Copilot execution exceeded timeout of {task.timeout}s")
            finally:
                with self._lock:
                    self._active_procs.pop(task.task_id, None)

            if proc.returncode != 0:
                err_msg = stderr.strip() or stdout.strip() or f"Copilot exited with code {proc.returncode}"
                raise RuntimeError(err_msg[:400])

            modified_files = []
            if getattr(task, "worktree", None) and Path(task.worktree).exists():
                st = subprocess.run(
                    ["git", "-C", task.worktree, "status", "--porcelain"],
                    capture_output=True, text=True
                ).stdout
                modified_files = [line.strip().split(maxsplit=1)[-1] for line in st.splitlines() if line.strip()]

            return {
                "status": "ok",
                "agent": "copilot",
                "model": "GPT-5.6 Luna",
                "version": "1.0.112",
                "task_id": task.task_id,
                "worktree": getattr(task, "worktree", None),
                "output": redact(stdout.strip()[:2000]),
                "modified_files": modified_files,
                "sandboxed": self.sandboxed,
            }
        except Exception as exc:
            logger.error("Copilot execution error for task %s: %s", task.task_id, exc)
            raise

    def cancel(self, task_id: Optional[str] = None):
        with self._lock:
            if task_id:
                proc = self._active_procs.get(task_id)
                if proc:
                    try:
                        proc.kill()
                    except Exception:
                        pass
            else:
                for proc in self._active_procs.values():
                    try:
                        proc.kill()
                    except Exception:
                        pass


class CodexCliAdapter:
    """
    Real non-interactive execution adapter using OpenAI Codex CLI (ChatGPT Plus).
    Enforces workspace-write sandboxing and detects rate/usage limits for intelligent failover.
    """
    integration_type = "real_cli"
    detail = "OpenAI Codex CLI (v0.167.1 · ChatGPT Plus)"

    def __init__(self, executable: Optional[str] = None, sandbox_mode: str = "workspace-write"):
        self.executable = executable or shutil.which("codex") or "/home/roshan/.local/bin/codex"
        self.sandbox_mode = sandbox_mode
        self._active_procs: Dict[str, subprocess.Popen] = {}
        self._lock = threading.Lock()
        self.rate_limited_until: Optional[float] = None

    def is_available(self) -> bool:
        return bool(self.executable and Path(self.executable).is_file() and os.access(self.executable, os.X_OK))

    def execute(self, task: Task) -> Dict[str, Any]:
        if not self.is_available():
            raise RuntimeError(f"Codex CLI executable not found at {self.executable}")

        work_dir = task.worktree if (getattr(task, "worktree", None) and Path(task.worktree).exists()) else str(Path.cwd())
        effective_sandbox = self.sandbox_mode if getattr(task, "worktree", None) else "read-only"

        cmd = [
            self.executable,
            "exec",
            "--skip-git-repo-check",
            "-C", work_dir,
            "-s", effective_sandbox,
            task.prompt,
        ]

        logger.info("Executing Codex task %s in %s (sandbox: %s)", task.task_id, work_dir, effective_sandbox)
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            with self._lock:
                self._active_procs[task.task_id] = proc

            try:
                stdout, stderr = proc.communicate(timeout=task.timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                raise TimeoutError(f"Codex execution exceeded timeout of {task.timeout}s")
            finally:
                with self._lock:
                    self._active_procs.pop(task.task_id, None)

            combined_out = (stdout + "\n" + stderr).strip()
            # Detect usage / rate limit errors
            if "usage limit" in combined_out.lower() or "rate limit" in combined_out.lower():
                import time
                self.rate_limited_until = time.time() + 3600.0  # 1 hour cooloff
                raise RateLimitError(f"Codex usage limit encountered: {combined_out[:300]}")

            if proc.returncode != 0:
                err_msg = stderr.strip() or stdout.strip() or f"Codex exited with code {proc.returncode}"
                raise RuntimeError(err_msg[:400])

            modified_files = []
            if getattr(task, "worktree", None) and Path(task.worktree).exists():
                st = subprocess.run(
                    ["git", "-C", task.worktree, "status", "--porcelain"],
                    capture_output=True, text=True
                ).stdout
                modified_files = [line.strip().split(maxsplit=1)[-1] for line in st.splitlines() if line.strip()]

            return {
                "status": "ok",
                "agent": "codex",
                "model": "gpt-6-luna",
                "version": "0.167.1",
                "task_id": task.task_id,
                "worktree": getattr(task, "worktree", None),
                "output": redact(stdout.strip()[:2000]),
                "modified_files": modified_files,
                "sandbox": effective_sandbox,
            }
        except Exception as exc:
            logger.error("Codex execution error for task %s: %s", task.task_id, exc)
            raise

    def cancel(self, task_id: Optional[str] = None):
        with self._lock:
            if task_id:
                proc = self._active_procs.get(task_id)
                if proc:
                    try:
                        proc.kill()
                    except Exception:
                        pass
            else:
                for proc in self._active_procs.values():
                    try:
                        proc.kill()
                    except Exception:
                        pass
