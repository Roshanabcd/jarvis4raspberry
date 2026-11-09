"""
JARVIS Desktop Program Runner
Executes local project programs (Python, Shell scripts, etc.) with real stdout,
stderr, exit-code capture, and background process tracking.
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("JARVIS-PROGRAM-RUNNER")


class DesktopProgramRunner:
    """Manages synchronous and background program execution with deterministic output."""

    def __init__(self) -> None:
        self._background_processes: Dict[str, Dict[str, Any]] = {}

    def run_program(
        self,
        file_path: str,
        working_dir: Optional[str] = None,
        args: Optional[List[str]] = None,
        timeout: int = 30,
        background: bool = False,
    ) -> Dict[str, Any]:
        """Execute a program file and return real execution metrics."""
        clean_p = os.path.realpath(os.path.expanduser(file_path.strip()))
        if not os.path.exists(clean_p):
            return {
                "success": False,
                "status": "file_not_found",
                "file_path": file_path,
                "error": f"Target file '{file_path}' does not exist on disk.",
                "exit_code": -1,
            }

        cwd = os.path.realpath(os.path.expanduser(working_dir)) if working_dir else os.path.dirname(clean_p)
        if not os.path.isdir(cwd):
            cwd = os.path.dirname(clean_p)

        ext = Path(clean_p).suffix.lower()
        if ext == ".py":
            cmd = ["python3", clean_p]
        elif ext in (".sh", ".bash"):
            cmd = ["bash", clean_p]
        elif ext in (".js", ".mjs"):
            cmd = ["node", clean_p]
        else:
            if os.access(clean_p, os.X_OK):
                cmd = [clean_p]
            else:
                cmd = ["python3", clean_p]

        if args:
            cmd.extend(args)

        t_start = time.time()
        job_id = f"job_{uuid.uuid4().hex[:8]}"

        if background:
            log_path = f"/tmp/jarvis_prog_{job_id}.log"
            log_fh = open(log_path, "w")
            proc = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid,
            )
            info = {
                "job_id": job_id,
                "pid": proc.pid,
                "command": cmd,
                "cwd": cwd,
                "log_file": log_path,
                "start_time": t_start,
                "status": "running",
            }
            self._background_processes[job_id] = info
            return {
                "success": True,
                "status": "started_background",
                "job_id": job_id,
                "pid": proc.pid,
                "log_file": log_path,
                "cwd": cwd,
                "command": " ".join(cmd),
            }

        try:
            res = subprocess.run(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
            )
            dur_ms = int((time.time() - t_start) * 1000)
            return {
                "success": res.returncode == 0,
                "status": "completed" if res.returncode == 0 else "failed",
                "file_path": clean_p,
                "cwd": cwd,
                "command": " ".join(cmd),
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "duration_ms": dur_ms,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "status": "timeout",
                "file_path": clean_p,
                "cwd": cwd,
                "command": " ".join(cmd),
                "exit_code": 124,
                "error": f"Execution timed out after {timeout} seconds.",
                "duration_ms": timeout * 1000,
            }
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "file_path": clean_p,
                "cwd": cwd,
                "command": " ".join(cmd),
                "exit_code": -1,
                "error": str(e),
                "duration_ms": int((time.time() - t_start) * 1000),
            }

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get tracking status for a specific background job."""
        if job_id not in self._background_processes:
            return None
        info = self._background_processes[job_id]
        pid = info.get("pid")
        try:
            os.kill(pid, 0)
            info["status"] = "running"
        except OSError:
            info["status"] = "finished"
        return info

    def stop_job(self, job_id: str) -> Dict[str, Any]:
        """Stop a tracked background process."""
        if job_id not in self._background_processes:
            return {"success": False, "error": f"Job ID '{job_id}' not found."}
        info = self._background_processes[job_id]
        pid = info.get("pid")
        try:
            os.kill(pid, 15)  # SIGTERM
            time.sleep(0.2)
            info["status"] = "stopped"
            return {"success": True, "job_id": job_id, "pid": pid, "status": "stopped"}
        except Exception as e:
            return {"success": False, "job_id": job_id, "error": str(e)}

    def list_jobs(self) -> List[Dict[str, Any]]:
        """List active and completed background jobs."""
        jobs = []
        for jid, info in list(self._background_processes.items()):
            pid = info.get("pid")
            running = False
            try:
                os.kill(pid, 0)
                running = True
            except OSError:
                running = False
            info["status"] = "running" if running else "finished"
            jobs.append(info)
        return jobs


program_runner = DesktopProgramRunner()
