"""Unit tests for GitHubCICDEngine (Module 27)."""

from __future__ import annotations

import hashlib
import hmac
import os
import tempfile
import unittest

from backend.app.config import GitHubCICDConfig
from backend.services.cicd_engine import GitHubCICDEngine, GitHubCICDError


class TestGitHubCICDEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = GitHubCICDConfig(
            db_path=os.path.join(self._tmp.name, "test_m27.db"),
            webhook_secret="unit-test-secret",
        )
        self.engine = GitHubCICDEngine(config=cfg)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_pr_merge_gate_and_release_rollback(self) -> None:
        repo = self.engine.register_repo({"full_name": "roshan/jarvis-os", "default_branch": "main"})
        pr = self.engine.create_pr(
            {"repo_id": repo["repo_id"], "title": "Feat CI Gate", "source_branch": "feat/ci", "target_branch": "main"}
        )

        # Merge must fail before CI passes
        with self.assertRaises(GitHubCICDError) as ctx:
            self.engine.merge_pr(pr["pr_id"])
        self.assertEqual(ctx.exception.code, "CI_GATE_BLOCKED")

        # Simulated CI failure keeps merge blocked
        fail_run = self.engine.trigger_pipeline(
            {"repo_id": repo["repo_id"], "pr_id": pr["pr_id"], "branch": "feat/ci", "simulate_failure": True}
        )
        self.assertEqual(fail_run["status"], "failed")
        with self.assertRaises(GitHubCICDError):
            self.engine.merge_pr(pr["pr_id"])

        # Passing CI unblocks merge & release
        pass_run = self.engine.trigger_pipeline(
            {"repo_id": repo["repo_id"], "pr_id": pr["pr_id"], "branch": "feat/ci", "simulate_failure": False}
        )
        self.assertEqual(pass_run["status"], "passed")
        merged = self.engine.merge_pr(pr["pr_id"], strategy="squash", merged_by="roshan")
        self.assertEqual(merged["status"], "merged")

        rel = self.engine.create_release({"repo_id": repo["repo_id"], "tag_name": "v1.0.0", "notes": "First release"})
        self.assertEqual(rel["status"], "published")
        rolled = self.engine.rollback_release(rel["release_id"])
        self.assertEqual(rolled["status"], "rolled_back")

    def test_webhook_hmac_verification(self) -> None:
        body = b'{"action":"opened"}'
        good_sig = "sha256=" + hmac.new(b"unit-test-secret", body, hashlib.sha256).hexdigest()
        self.assertTrue(self.engine.verify_webhook_signature(body, good_sig))
        self.assertFalse(self.engine.verify_webhook_signature(body, "sha256=deadbeef"))
        self.assertFalse(self.engine.verify_webhook_signature(body, None))

    def test_invalid_repo_name_rejected(self) -> None:
        with self.assertRaises(GitHubCICDError) as ctx:
            self.engine.register_repo({"full_name": "invalid-no-slash"})
        self.assertEqual(ctx.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
