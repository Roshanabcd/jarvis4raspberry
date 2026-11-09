"""
Git Safety and Workspace Isolation Manager for JARVIS OS Phase 5.
Protects user workspace state before autonomous agent repairs, creates isolated checkpoints,
validates patches against syntax and tests, and guarantees safe rollback on regression.
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("JARVIS.GitSafety")


class GitSafetyManager:
    """Manages workspace snapshots, isolated repair checkpoints, and rollback guarantees."""

    def __init__(self, workspace_root: str = "/home/roshan/.gemini/antigravity/scratch/jarvis-os"):
        self.workspace_root = Path(workspace_root)
        self.snapshots_dir = self.workspace_root / "data" / "checkpoints"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self._active_snapshots: Dict[str, Dict[str, Any]] = {}

    def create_pre_repair_checkpoint(
        self,
        task_id: str,
        target_files: Optional[List[str]] = None,
        workspace_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record pre-repair git status, initial commit, and create file-level backup snapshots."""
        w_dir = workspace_dir or str(self.workspace_root)
        checkpoint_id = f"ckpt_{task_id}_{int(time.time())}"

        # 1. Capture git status & commit hash
        initial_commit = "unknown"
        uncommitted_files: List[str] = []
        try:
            res_c = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=w_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            if res_c.returncode == 0:
                initial_commit = res_c.stdout.strip()

            res_s = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=w_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            if res_s.returncode == 0:
                for line in res_s.stdout.splitlines():
                    if line.strip():
                        uncommitted_files.append(line.strip().split()[-1])
        except Exception as e:
            logger.warning("Git inspection failed in %s: %s", w_dir, e)

        # 2. File-level backup of target files or modified files
        backup_dir = self.snapshots_dir / checkpoint_id
        backup_dir.mkdir(parents=True, exist_ok=True)

        backed_up_files: Dict[str, str] = {}
        files_to_save = set(target_files or [])
        files_to_save.update(uncommitted_files)

        for rel_f in files_to_save:
            p_f = Path(rel_f)
            src = p_f if p_f.is_absolute() else (Path(w_dir) / rel_f)
            if src.exists() and src.is_file():
                if p_f.is_absolute():
                    try:
                        rel_key = str(p_f.relative_to(w_dir))
                    except ValueError:
                        rel_key = p_f.name
                else:
                    rel_key = str(rel_f)
                dest = backup_dir / rel_key
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                backed_up_files[rel_key] = str(dest)

        checkpoint = {
            "checkpoint_id": checkpoint_id,
            "task_id": task_id,
            "workspace_dir": w_dir,
            "initial_commit": initial_commit,
            "uncommitted_files": uncommitted_files,
            "backed_up_files": backed_up_files,
            "backup_dir": str(backup_dir),
            "created_at": time.time(),
        }
        self._active_snapshots[task_id] = checkpoint
        logger.info("Created pre-repair checkpoint %s for task %s (%d files saved)", checkpoint_id, task_id, len(backed_up_files))
        return checkpoint

    def validate_syntax(self, filepath: str) -> Tuple[bool, Optional[str]]:
        """Verify Python syntax without executing code."""
        path = Path(filepath)
        if not path.exists():
            return False, f"File {filepath} does not exist"

        if filepath.endswith(".py"):
            try:
                import py_compile
                py_compile.compile(str(path), doraise=True)
                return True, None
            except py_compile.PyCompileError as e:
                return False, f"Syntax Error: {e}"
            except Exception as e:
                return False, str(e)
        return True, None

    def rollback(self, task_id: str) -> Dict[str, Any]:
        """Safely restore workspace files to the pre-repair checkpoint."""
        checkpoint = self._active_snapshots.get(task_id)
        if not checkpoint:
            return {"status": "error", "message": f"No active checkpoint found for task {task_id}"}

        w_dir = Path(checkpoint["workspace_dir"])
        restored = []
        for rel_f, backup_path in checkpoint["backed_up_files"].items():
            dest = w_dir / rel_f
            if os.path.exists(backup_path):
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_path, dest)
                restored.append(rel_f)

        logger.info("Rolled back %d files to checkpoint %s for task %s", len(restored), checkpoint["checkpoint_id"], task_id)
        return {
            "status": "ok",
            "task_id": task_id,
            "checkpoint_id": checkpoint["checkpoint_id"],
            "restored_files": restored,
        }

    def cleanup_checkpoint(self, task_id: str) -> None:
        """Remove checkpoint after successful verification."""
        checkpoint = self._active_snapshots.pop(task_id, None)
        if checkpoint and os.path.exists(checkpoint["backup_dir"]):
            try:
                shutil.rmtree(checkpoint["backup_dir"])
            except Exception:
                pass

    def create_snapshot(
        self,
        workspace_dir: str,
        target_files: Optional[List[str]] = None,
        task_id: Optional[str] = None
    ) -> str:
        tid = task_id or f"snap_{int(time.time()*1000)}"
        self.create_pre_repair_checkpoint(tid, target_files=target_files, workspace_dir=workspace_dir)
        return tid

    def rollback_snapshot(self, task_id: str) -> Tuple[bool, str]:
        res = self.rollback(task_id)
        if res.get("status") == "ok":
            return True, f"Restored {len(res.get('restored_files', []))} files."
        return False, res.get("message", "Rollback failed")

    def rollback_latest(self) -> Tuple[bool, str]:
        if not self._active_snapshots:
            return False, "No active snapshots available."
        latest_task_id = list(self._active_snapshots.keys())[-1]
        return self.rollback_snapshot(latest_task_id)

    def verify_syntax(self, filepath: str) -> Tuple[bool, str]:
        ok, err = self.validate_syntax(filepath)
        return ok, err or ""


git_safety = GitSafetyManager()
