"""Integration tests for mounting Module 29 into a host JARVIS OS FastAPI app."""

from __future__ import annotations

import os
import tempfile
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.module_29_advanced_file_manager.backend.app.config import FileManagerConfig
from modules.module_29_advanced_file_manager.backend.app.main import mount_module
from modules.module_29_advanced_file_manager.backend.services.file_engine import FileManagerEngine


class TestHostMountIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.host_app = FastAPI(title="Simulated JARVIS OS Host")

        @self.host_app.get("/")
        async def host_root():
            return {"host": "jarvis-os-core"}

        cfg = FileManagerConfig(
            db_path=os.path.join(self._tmp.name, "host_m29.db"),
            root_dir=os.path.join(self._tmp.name, "managed_files"),
        )
        engine = FileManagerEngine(config=cfg)
        mount_module(self.host_app, engine=engine, include_root_ui=False)
        self.client = TestClient(self.host_app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_host_root_preserved_and_module_mounted(self) -> None:
        r_root = self.client.get("/")
        self.assertEqual(r_root.status_code, 200)
        self.assertEqual(r_root.json()["host"], "jarvis-os-core")

        r_ui = self.client.get("/file-manager")
        self.assertEqual(r_ui.status_code, 200)
        self.assertIn("Module 29", r_ui.text)

        r_health = self.client.get("/api/v1/file-manager/health")
        self.assertEqual(r_health.status_code, 200)
        self.assertEqual(r_health.json()["status"], "ok")

    def test_persistence_across_engine_restarts(self) -> None:
        db_path = os.path.join(self._tmp.name, "persist_m29.db")
        root_dir = os.path.join(self._tmp.name, "persist_files")
        eng1 = FileManagerEngine(config=FileManagerConfig(db_path=db_path, root_dir=root_dir))
        eng1.write_file("doc.txt", "persistent")
        eng1.db.set_tags("doc.txt", ["archive"])

        eng2 = FileManagerEngine(config=FileManagerConfig(db_path=db_path, root_dir=root_dir))
        self.assertEqual(eng2.read_file("doc.txt")["content"], "persistent")
        self.assertEqual(eng2.db.get_all_tags()["doc.txt"], ["archive"])


if __name__ == "__main__":
    unittest.main()
