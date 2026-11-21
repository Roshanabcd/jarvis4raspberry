"""REST & WebSocket API tests for JARVIS Module 27 — GitHub & CI/CD Manager."""

from __future__ import annotations

import hashlib
import hmac
import os
import tempfile
import unittest

from fastapi.testclient import TestClient

from modules.module_27_github_cicd_manager.backend.app.config import GitHubCICDConfig
from modules.module_27_github_cicd_manager.backend.app.main import create_app


class TestGitHubCICDAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = GitHubCICDConfig(
            db_path=os.path.join(self._tmp.name, "api_m27.db"),
            webhook_secret="api-webhook-secret",
        )
        self.app = create_app(config=cfg)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_manifest_and_ui(self) -> None:
        r_h = self.client.get("/api/v1/github-cicd/health")
        self.assertEqual(r_h.status_code, 200)
        self.assertEqual(r_h.json()["module_id"], "jarvis-module-27-github-cicd-manager")
        self.assertTrue(r_h.json()["simulated"])

        r_m = self.client.get("/api/v1/github-cicd/manifest")
        self.assertEqual(r_m.status_code, 200)
        self.assertEqual(r_m.json()["version"], "1.0.0")

        r_ui = self.client.get("/github-cicd")
        self.assertEqual(r_ui.status_code, 200)
        self.assertIn("GitHub &amp; CI/CD Manager", r_ui.text)

    def test_full_rest_workflow_and_webhook_auth(self) -> None:
        r_repo = self.client.post("/api/v1/github-cicd/repos", json={"full_name": "roshan/jarvis-core"})
        self.assertEqual(r_repo.status_code, 201)
        repo_id = r_repo.json()["repo_id"]

        r_pr = self.client.post(
            "/api/v1/github-cicd/pull-requests",
            json={"repo_id": repo_id, "title": "Add module 27", "source_branch": "feat/m27", "target_branch": "main"},
        )
        self.assertEqual(r_pr.status_code, 201)
        pr_id = r_pr.json()["pr_id"]

        blocked = self.client.post(f"/api/v1/github-cicd/pull-requests/{pr_id}/merge", json={"strategy": "squash"})
        self.assertEqual(blocked.status_code, 409)

        run = self.client.post(
            "/api/v1/github-cicd/pipelines/trigger",
            json={"repo_id": repo_id, "pr_id": pr_id, "branch": "feat/m27"},
        )
        self.assertEqual(run.status_code, 201)
        self.assertEqual(run.json()["status"], "passed")

        merged = self.client.post(f"/api/v1/github-cicd/pull-requests/{pr_id}/merge", json={"strategy": "squash"})
        self.assertEqual(merged.status_code, 200)
        self.assertEqual(merged.json()["status"], "merged")

        rel = self.client.post("/api/v1/github-cicd/releases", json={"repo_id": repo_id, "tag_name": "v1.0.0"})
        self.assertEqual(rel.status_code, 201)
        rb = self.client.post(f"/api/v1/github-cicd/releases/{rel.json()['release_id']}/rollback")
        self.assertEqual(rb.status_code, 200)
        self.assertEqual(rb.json()["status"], "rolled_back")

        payload = b'{"ref":"refs/heads/main"}'
        sig = "sha256=" + hmac.new(b"api-webhook-secret", payload, hashlib.sha256).hexdigest()
        bad_wh = self.client.post("/api/v1/github-cicd/webhooks/github", data=payload, headers={"X-Hub-Signature-256": "sha256=bad"})
        self.assertEqual(bad_wh.status_code, 401)
        ok_wh = self.client.post(
            "/api/v1/github-cicd/webhooks/github",
            data=payload,
            headers={"X-Hub-Signature-256": sig, "X-GitHub-Event": "push"},
        )
        self.assertEqual(ok_wh.status_code, 200)
        self.assertTrue(ok_wh.json()["accepted"])

    def test_websocket_connects(self) -> None:
        with self.client.websocket_connect("/api/v1/github-cicd/ws/events") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")
            self.assertIn("status", msg)


if __name__ == "__main__":
    unittest.main()
