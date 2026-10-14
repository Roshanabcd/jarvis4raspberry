"""Git version control tools for JARVIS OS.

Executes git commands strictly through the SecureCommandRunner allowlist,
enforcing workspace boundary validation, risk levels, and confirmation gates.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from config.config_manager import config
from tools.filesystem.file_tools import file_tools
from tools.shell.command_runner import command_runner, SecureCommandRunner

logger = logging.getLogger("JARVIS-GIT")


class GitTools:
    """Git version control automation wrapper utilizing SecureCommandRunner."""

    def __init__(self, runner: Optional[SecureCommandRunner] = None) -> None:
        """Initialize GitTools.

        Args:
            runner: Optional SecureCommandRunner instance.
        """
        self.runner = runner or command_runner

    def _validate_repo_path(self, repo_path: str) -> str:
        """Validate and resolve repository path within workspace limits."""
        return file_tools.validate_path(repo_path)

    def clone(self, url: str, path: str) -> Dict[str, Any]:
        """Clone a remote repository into a target workspace directory.

        Args:
            url: Git repository URL (https/ssh).
            path: Destination directory path.

        Returns:
            Command execution output dictionary.
        """
        safe_path = self._validate_repo_path(path)
        simulated = config.get("simulation_mode", True)

        if simulated:
            logger.info(f"[SIM] Simulating git clone '{url}' into '{safe_path}'")
            return {
                "success": True,
                "returncode": 0,
                "stdout": f"[SIMULATION] Repository '{url}' cloned to '{safe_path}'.",
                "stderr": "",
                "simulated": True,
            }

        logger.info(f"Cloning repo '{url}' -> '{safe_path}'")
        res = self.runner.execute_command("git", ["clone", url, safe_path], timeout=120)
        res["success"] = res["returncode"] == 0
        return res

    def status(self, repo_path: str) -> Dict[str, Any]:
        """Query working tree status of a git repository.

        Args:
            repo_path: Path to git repository.

        Returns:
            Dictionary with status output and success flag.
        """
        safe_path = self._validate_repo_path(repo_path)
        res = self.runner.execute_command("git", ["-C", safe_path, "status", "--short", "--branch"])
        res["success"] = res["returncode"] == 0
        return res

    def log(self, repo_path: str, n: int = 10) -> Dict[str, Any]:
        """Retrieve recent commit history.

        Args:
            repo_path: Path to git repository.
            n: Number of log entries to retrieve (default: 10).

        Returns:
            Dictionary containing log output.
        """
        safe_path = self._validate_repo_path(repo_path)
        count = max(1, min(int(n), 100))
        res = self.runner.execute_command(
            "git",
            ["-C", safe_path, "log", f"-n{count}", "--pretty=format:%h - %an, %ar : %s"],
        )
        res["success"] = res["returncode"] == 0
        return res

    def diff(self, repo_path: str) -> Dict[str, Any]:
        """Inspect unstaged diffs in repository.

        Args:
            repo_path: Path to git repository.

        Returns:
            Dictionary containing git diff output.
        """
        safe_path = self._validate_repo_path(repo_path)
        res = self.runner.execute_command("git", ["-C", safe_path, "diff"])
        res["success"] = res["returncode"] == 0
        return res

    def checkout(self, repo_path: str, branch: str) -> Dict[str, Any]:
        """Switch branches or restore working tree files.

        Args:
            repo_path: Path to git repository.
            branch: Branch name to checkout.

        Returns:
            Dictionary with checkout command results.
        """
        safe_path = self._validate_repo_path(repo_path)
        clean_branch = branch.strip()
        if not clean_branch or any(c in clean_branch for c in (";", "&", "|", "`", "$", " ")):
            raise ValueError(f"Invalid branch name: '{branch}'")

        res = self.runner.execute_command("git", ["-C", safe_path, "checkout", clean_branch])
        res["success"] = res["returncode"] == 0
        return res

    def commit(self, repo_path: str, message: str) -> Dict[str, Any]:
        """Stage all changes and record a new commit.

        Risk Level: 2 (Modifies repository history).

        Args:
            repo_path: Path to git repository.
            message: Commit log message.

        Returns:
            Dictionary with commit output.
        """
        safe_path = self._validate_repo_path(repo_path)
        clean_msg = message.strip()
        if not clean_msg:
            raise ValueError("Commit message cannot be empty.")

        simulated = config.get("simulation_mode", True)
        if simulated:
            logger.info(f"[SIM] Simulating git commit in '{safe_path}' with message: {clean_msg}")
            return {
                "success": True,
                "returncode": 0,
                "stdout": f"[SIMULATION] Staged and committed with message: '{clean_msg}'",
                "stderr": "",
                "simulated": True,
            }

        # Stage all tracked/untracked changes
        add_res = self.runner.execute_command("git", ["-C", safe_path, "add", "-A"])
        if add_res["returncode"] != 0:
            add_res["success"] = False
            return add_res

        res = self.runner.execute_command("git", ["-C", safe_path, "commit", "-m", clean_msg])
        res["success"] = res["returncode"] == 0
        return res

    def push(
        self,
        repo_path: str,
        confirmed: bool = False,
        remote: str = "origin",
        branch: str = "",
    ) -> Dict[str, Any]:
        """Push commits to a remote upstream repository.

        Risk Level: 3 (High Risk: Modifies external shared repository state).
        Requires explicit confirmation flag.

        Args:
            repo_path: Path to git repository.
            confirmed: Explicit confirmation flag (must be True).
            remote: Remote repository name (default: "origin").
            branch: Optional remote branch name.

        Returns:
            Dictionary describing push results.

        Raises:
            PermissionError: If confirmed is not True.
        """
        if not confirmed:
            raise PermissionError(
                "Confirmation required: 'push' operation is Risk Level 3 and requires confirmed=True."
            )

        safe_path = self._validate_repo_path(repo_path)
        simulated = config.get("simulation_mode", True)

        if simulated:
            logger.warning(f"[SIM] Simulating git push to '{remote}' from '{safe_path}' (confirmed=True)")
            return {
                "success": True,
                "returncode": 0,
                "stdout": f"[SIMULATION] Pushed commits to remote '{remote}'.",
                "stderr": "",
                "simulated": True,
            }

        args = ["-C", safe_path, "push", remote]
        if branch.strip():
            args.append(branch.strip())

        res = self.runner.execute_command("git", args, timeout=60)
        res["success"] = res["returncode"] == 0
        return res


# Global instance
git_tools = GitTools()
