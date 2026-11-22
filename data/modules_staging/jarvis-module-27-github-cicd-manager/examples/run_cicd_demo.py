"""Runnable CLI demonstration for JARVIS Module 27 — GitHub & CI/CD Manager."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import GitHubCICDConfig
from backend.services.cicd_engine import GitHubCICDEngine, GitHubCICDError


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cfg = GitHubCICDConfig(db_path=os.path.join(tmp, "demo_m27.db"))
        engine = GitHubCICDEngine(config=cfg)

        repo = engine.register_repo({"full_name": "roshan/jarvis-os", "default_branch": "main"})
        pr = engine.create_pr(
            {
                "repo_id": repo["repo_id"],
                "title": "Add Module 27 GitHub & CI/CD Manager",
                "source_branch": "feat/module-27",
                "target_branch": "main",
                "author": "roshan",
            }
        )
        print(f"Registered Repo : {repo['full_name']} ({repo['repo_id']})")
        print(f"Opened PR       : #{pr['pr_number']} {pr['title']} (ci={pr['ci_status']})")

        try:
            engine.merge_pr(pr["pr_id"])
        except GitHubCICDError as exc:
            print(f"CI Gate Check   : Blocked as expected ({exc.code})")

        run = engine.trigger_pipeline(
            {"repo_id": repo["repo_id"], "pr_id": pr["pr_id"], "workflow_name": "ci-test", "branch": "feat/module-27"}
        )
        merged = engine.merge_pr(pr["pr_id"], strategy="squash", merged_by="roshan")
        rel = engine.create_release({"repo_id": repo["repo_id"], "tag_name": "v1.0.0", "notes": "Module 27 release"})
        print(f"CI Run Status   : {run['status']} ({run['duration_sec']}s)")
        print(f"PR Merged       : #{merged['pr_number']} -> {merged['status']} ({merged['merge_strategy']})")
        print(f"Release Created : {rel['tag_name']} ({rel['status']})")


if __name__ == "__main__":
    main()
