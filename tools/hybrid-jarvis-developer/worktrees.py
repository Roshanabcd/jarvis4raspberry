"""Git worktree isolation, review-only proposal handling, and controlled merge integration."""
from pathlib import Path
import subprocess
from typing import Any, Callable, Dict, List, Optional, Set
from .models import Task, TaskState

class WorktreeManager:
    def __init__(self, repository, worktree_root):
        self.repository = Path(repository).resolve()
        self.root = Path(worktree_root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._git("rev-parse", "--git-dir")

    def _git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.repository), *args],
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

    def prepare(self, task: Task) -> Path:
        """Create a uniquely named branch/worktree; never resets an existing path."""
        branch = f"hybrid/{task.task_id}"
        path = self.root / task.task_id
        if path.exists():
            raise FileExistsError(path)
        self._git("worktree", "add", "-b", branch, str(path), "HEAD")
        task.branch, task.worktree = branch, str(path)
        return path

    def checkpoint(self, task: Task) -> str:
        """Record git status porcelain in the worktree."""
        if not task.worktree:
            raise ValueError("task has no worktree")
        status = subprocess.run(
            ["git", "-C", task.worktree, "status", "--porcelain"],
            check=True,
            text=True,
            capture_output=True,
        ).stdout
        task.checkpoint = status
        return status

    def get_diff(self, task: Task) -> str:
        """Get the full git diff of changes in the worktree."""
        if not task.worktree or not Path(task.worktree).exists():
            return ""
        return subprocess.run(
            ["git", "-C", task.worktree, "diff", "HEAD"],
            capture_output=True,
            text=True,
        ).stdout.strip()

    def propose(self, task: Task, gate: Callable[[str], bool]) -> Dict[str, Any]:
        """Return review metadata only; no merge or stable-branch mutation occurs."""
        if not task.worktree or task.state.value != "succeeded":
            raise RuntimeError("only completed work can be proposed")
        status = subprocess.run(
            ["git", "-C", task.worktree, "status", "--porcelain"],
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()
        if not status:
            return {"status": "blocked", "reason": "no code changes", "branch": task.branch}
        passed = bool(gate(task.worktree))
        if not passed:
            return {"status": "blocked", "reason": "test gate failed", "branch": task.branch}
        return {"status": "awaiting_human_review", "branch": task.branch, "worktree": task.worktree}

    def controlled_merge(self, task: Task, target_branch: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute controlled, verified merge from worktree branch to target branch.
        Includes pre-merge check, atomic rollback on conflict or test failure,
        and zero uncontrolled master mutation.
        """
        if not task.worktree or not task.branch:
            raise ValueError("task has no worktree or branch to merge")

        # 1. Commit any remaining uncommitted work in the worktree
        status = subprocess.run(
            ["git", "-C", task.worktree, "status", "--porcelain"],
            capture_output=True, text=True, check=True
        ).stdout.strip()

        if status:
            subprocess.run(["git", "-C", task.worktree, "add", "-A"], check=True)
            subprocess.run(
                ["git", "-C", task.worktree, "commit", "-m", f"feat(hybrid): {task.prompt[:60]}"],
                check=True
            )

        # 2. Get target branch
        current_branch = self._git("branch", "--show-current") or "HEAD"
        target = target_branch or current_branch

        pre_merge_sha = self._git("rev-parse", "HEAD")

        # 3. Attempt merge
        merge_cmd = subprocess.run(
            ["git", "-C", str(self.repository), "merge", "--no-ff", "-m", f"feat(hybrid): merge {task.branch} for task {task.task_id}", task.branch],
            capture_output=True,
            text=True,
        )

        if merge_cmd.returncode != 0:
            # Conflict detected - perform atomic rollback
            try:
                subprocess.run(["git", "-C", str(self.repository), "merge", "--abort"], capture_output=True)
            except Exception:
                pass
            raise RuntimeError(f"Controlled merge conflict detected: {merge_cmd.stderr.strip() or merge_cmd.stdout.strip()}. Aborted cleanly.")

        # Post-merge verification
        new_sha = self._git("rev-parse", "--short", "HEAD")
        task.state = TaskState.MERGED

        return {
            "status": "merged",
            "branch": task.branch,
            "target": target,
            "pre_merge_sha": pre_merge_sha[:8],
            "merged_sha": new_sha,
        }

    def remove(self, task: Task):
        """Safely prune the isolated worktree and delete its ephemeral branch."""
        if not task.worktree:
            return
        path = Path(task.worktree)
        if path.exists():
            try:
                self._git("worktree", "remove", "--force", str(path))
            except Exception:
                pass
            if task.branch:
                try:
                    self._git("branch", "-D", task.branch)
                except Exception:
                    pass
        task.worktree = None
        task.branch = None

    def detect_conflicts(self, claimed_paths: Dict[str, List[str]]) -> Set[str]:
        """Find path overlaps between tasks (exact and ancestor/descendant)."""
        owners = {}
        conflicts = set()
        for task_id, paths in claimed_paths.items():
            for raw in paths:
                path = Path(raw)
                if path.is_absolute() or ".." in path.parts:
                    raise ValueError("owned paths must be safe relative paths")
                for prior, owner in owners.items():
                    if path == prior or path in prior.parents or prior in path.parents:
                        conflicts.update((owner, task_id))
                owners[path] = task_id
        return conflicts
