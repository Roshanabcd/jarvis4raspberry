"""Integration tests for mounting Module 27 into a host JARVIS OS FastAPI app."""

from __future__ import annotations

import os
import tempfile
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.module_27_github_cicd_manager.backend.app.config import GitHubCICDConfig
from modules.module_27_github_cicd_manager.backend.app.main import mount_module
from modules.module_27_github_cicd_manager.backend.services.cicd_engine import GitHubCICDEngine


class TestHostMountIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.host_app = FastAPI(title="Simulated JARVIS OS Host")

        @self.host_app.get("/")
        async def host_root():
            return {"host": "jarvis-os-core"}

        cfg = GitHubCICDConfig(db_path=os.path.join(self._tmp.name, "host_m27.db"))
        engine = GitHubCICDEngine(config=cfg)
        mount_module(self.host_app, engine=engine, include_root_ui=False)
        self.client = TestClient(self.host_app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_host_root_preserved_and_module_mounted(self) -> None:
        r_root = self.client.get("/")
        self.assertEqual(r_root.status_code, 200)
        self.assertEqual(r_root.json()["host"], "jarvis-os-core")

        r_ui = self.client.get("/github-cicd")
        self.assertEqual(r_ui.status_code, 200)
        self.assertIn("Module 27", r_ui.text)

        r_health = self.client.get("/api/v1/github-cicd/health")
        self.assertEqual(r_health.status_code, 200)
        self.assertEqual(r_health.json()["status"], "ok")

    def test_persistence_across_engine_restarts(self) -> None:
        db_path = os.path.join(self._tmp.name, "persist_m27.db")
        eng1 = GitHubCICDEngine(config=GitHubCICDConfig(db_path=db_path))
        repo = eng1.register_repo({"full_name": "roshan/persist-repo"})
        eng1.trigger_pipeline({"repo_id": repo["repo_id"], "branch": "main"})

        eng2 = GitHubCICDEngine(config=GitHubCICDConfig(db_path=db_path))
        self.assertEqual(len(eng2.db.list_repos()), 1)
        self.assertEqual(len(eng2.db.list_runs(repo_id=repo["repo_id"])), 1)


if __name__ == "__main__":
    unittest.main()
