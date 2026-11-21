"""GitHub & CI/CD Manager Engine (Module 27).

Provides:
- Repository registration & workflow policy tracking
- Pull request creation & branch-protection merge gates (requires passing CI)
- CI/CD pipeline execution with structured step logs and failure simulation
- Semantic release publishing & rollback tracking
- Real HMAC-SHA256 GitHub webhook signature verification
"""

from __future__ import annotations

import hashlib
import hmac
import time
import uuid
from typing import Any, Dict, Optional

from modules.module_27_github_cicd_manager.backend.adapters.github_adapter import GitHubCICDAdapter, SimulatedGitHubCICDAdapter
from modules.module_27_github_cicd_manager.backend.app.config import GitHubCICDConfig
from modules.module_27_github_cicd_manager.backend.models.database import GitHubCICDDB, utc_now_iso


class GitHubCICDError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class GitHubCICDEngine:
    def __init__(
        self,
        config: Optional[GitHubCICDConfig] = None,
        db: Optional[GitHubCICDDB] = None,
        adapter: Optional[GitHubCICDAdapter] = None,
    ) -> None:
        self.config = config or GitHubCICDConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or GitHubCICDDB(self.config.db_path)
        self.adapter = adapter or SimulatedGitHubCICDAdapter()
        self._started_at = time.monotonic()

    def _require_repo(self, repo_id: str) -> Dict[str, Any]:
        repo = self.db.get_repo(repo_id)
        if not repo:
            raise GitHubCICDError("REPO_NOT_FOUND", f"Repository '{repo_id}' not found.", 404)
        return repo

    def _require_pr(self, pr_id: str) -> Dict[str, Any]:
        pr = self.db.get_pr(pr_id)
        if not pr:
            raise GitHubCICDError("PR_NOT_FOUND", f"Pull request '{pr_id}' not found.", 404)
        return pr

    def register_repo(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        full_name = payload["full_name"].strip()
        if "/" not in full_name:
            raise GitHubCICDError("INVALID_REPO_NAME", "Repository full_name must use 'owner/repo' format.", 400)
        if self.db.get_repo_by_name(full_name):
            raise GitHubCICDError("REPO_EXISTS", f"Repository '{full_name}' is already registered.", 409)
        return self.db.create_repo(
            {
                "repo_id": f"repo_{uuid.uuid4().hex[:10]}",
                "full_name": full_name,
                "default_branch": payload.get("default_branch", "main"),
                "require_ci_green": bool(payload.get("require_ci_green", True)),
                "workflows": list(payload.get("workflows") or ["ci-test", "security-scan"]),
                "created_at": utc_now_iso(),
            }
        )

    def create_pr(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._require_repo(payload["repo_id"])
        num = self.db.next_pr_number(payload["repo_id"])
        return self.db.create_pr(
            {
                "pr_id": f"pr_{uuid.uuid4().hex[:10]}",
                "repo_id": payload["repo_id"],
                "pr_number": num,
                "title": payload["title"].strip(),
                "source_branch": payload["source_branch"].strip(),
                "target_branch": payload.get("target_branch", "main").strip(),
                "author": payload.get("author", "roshan").strip(),
                "files_changed": int(payload.get("files_changed", 1)),
                "status": "open",
                "ci_status": "pending",
                "created_at": utc_now_iso(),
            }
        )

    def trigger_pipeline(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        repo = self._require_repo(payload["repo_id"])
        pr_id = payload.get("pr_id")
        if pr_id:
            self._require_pr(pr_id)

        result = self.adapter.run_workflow(
            repo_full_name=repo["full_name"],
            workflow_name=payload.get("workflow_name", "ci-test"),
            branch=payload.get("branch", repo["default_branch"]),
            simulate_failure=bool(payload.get("simulate_failure", False)),
        )
        run = self.db.create_run(
            {
                "run_id": f"run_{uuid.uuid4().hex[:10]}",
                "repo_id": repo["repo_id"],
                "pr_id": pr_id,
                "workflow_name": payload.get("workflow_name", "ci-test"),
                "branch": payload.get("branch", repo["default_branch"]),
                "status": result["status"],
                "duration_sec": result["duration_sec"],
                "steps": result["steps"],
                "simulated": result["simulated"],
                "created_at": utc_now_iso(),
            }
        )
        if pr_id:
            self.db.update_pr(pr_id, ci_status=result["status"])
        return run

    def merge_pr(self, pr_id: str, strategy: str = "squash", merged_by: str = "operator") -> Dict[str, Any]:
        pr = self._require_pr(pr_id)
        if pr["status"] != "open":
            raise GitHubCICDError("PR_NOT_OPEN", f"Pull request '{pr_id}' is already '{pr['status']}'.", 409)
        repo = self._require_repo(pr["repo_id"])
        if repo["require_ci_green"] and pr["ci_status"] != "passed":
            raise GitHubCICDError(
                "CI_GATE_BLOCKED",
                f"Cannot merge PR #{pr['pr_number']}: required CI status is 'passed', current is '{pr['ci_status']}'.",
                409,
                details={"ci_status": pr["ci_status"]},
            )
        merged = self.db.update_pr(
            pr_id,
            status="merged",
            merge_strategy=f"{strategy}:{merged_by}",
            merged_at=utc_now_iso(),
        )
        return merged  # type: ignore[return-value]

    def create_release(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        repo = self._require_repo(payload["repo_id"])
        runs = self.db.list_runs(repo_id=repo["repo_id"])
        if repo["require_ci_green"] and not any(r["status"] == "passed" for r in runs):
            raise GitHubCICDError("RELEASE_BLOCKED", "At least one passing CI run is required before publishing a release.", 409)
        return self.db.create_release(
            {
                "release_id": f"rel_{uuid.uuid4().hex[:10]}",
                "repo_id": repo["repo_id"],
                "tag_name": payload["tag_name"].strip(),
                "notes": payload.get("notes", "").strip(),
                "status": "published",
                "created_at": utc_now_iso(),
            }
        )

    def rollback_release(self, release_id: str) -> Dict[str, Any]:
        updated = self.db.update_release_status(release_id, "rolled_back")
        if not updated:
            raise GitHubCICDError("RELEASE_NOT_FOUND", f"Release '{release_id}' not found.", 404)
        return updated

    def verify_webhook_signature(self, raw_body: bytes, signature_header: Optional[str]) -> bool:
        if not signature_header or not signature_header.startswith("sha256="):
            return False
        expected = "sha256=" + hmac.new(
            self.config.webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature_header)

    def get_status(self) -> Dict[str, Any]:
        repos = self.db.list_repos()
        prs = self.db.list_prs()
        runs = self.db.list_runs()
        releases = self.db.list_releases()
        return {
            "adapter": self.adapter.adapter_name,
            "simulated": self.adapter.is_simulated,
            "repositories_count": len(repos),
            "open_prs": sum(1 for p in prs if p["status"] == "open"),
            "merged_prs": sum(1 for p in prs if p["status"] == "merged"),
            "pipeline_runs": len(runs),
            "failed_runs": sum(1 for r in runs if r["status"] == "failed"),
            "releases_count": len(releases),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
