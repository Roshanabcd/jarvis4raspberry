"""GitHub & CI/CD provider adapter contract for Module 27."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class GitHubCICDAdapter(ABC):
    adapter_name: str = "abstract_github_cicd"
    is_simulated: bool = True

    @abstractmethod
    def run_workflow(self, repo_full_name: str, workflow_name: str, branch: str, simulate_failure: bool = False) -> Dict[str, Any]:
        """Execute (or simulate) a CI/CD workflow and return status, duration_sec, and step logs."""


class SimulatedGitHubCICDAdapter(GitHubCICDAdapter):
    """Deterministic local GitHub Actions / CI runner simulator (no GitHub PAT required)."""

    adapter_name = "simulated_github_actions_adapter"
    is_simulated = True

    def run_workflow(self, repo_full_name: str, workflow_name: str, branch: str, simulate_failure: bool = False) -> Dict[str, Any]:
        steps: List[Dict[str, Any]] = [
            {"step": "checkout", "status": "passed", "duration_sec": 1.2, "log": f"Checked out {repo_full_name}@{branch}"},
            {"step": "lint_and_typecheck", "status": "passed", "duration_sec": 3.4, "log": "Static analysis clean (0 errors)"},
            {
                "step": "automated_tests",
                "status": "failed" if simulate_failure else "passed",
                "duration_sec": 6.8,
                "log": "Simulated test failure triggered by request" if simulate_failure else "All test suites passed",
            },
            {
                "step": "security_and_package",
                "status": "skipped" if simulate_failure else "passed",
                "duration_sec": 0.0 if simulate_failure else 2.5,
                "log": "Skipped due to upstream test failure" if simulate_failure else f"Workflow '{workflow_name}' artifact verified",
            },
        ]
        total_sec = round(sum(s["duration_sec"] for s in steps), 2)
        return {
            "status": "failed" if simulate_failure else "passed",
            "duration_sec": total_sec,
            "steps": steps,
            "simulated": True,
        }
