"""Integration tests for mounting Module 38 inside a host JARVIS OS FastAPI app."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.config import MarketplaceConfig
from backend.app.main import mount_module
from backend.services.marketplace_engine import MarketplaceEngine


class TestModule38Integration(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = MarketplaceConfig(db_path=str(Path(self._tmp.name) / "host_marketplace.db"))
        self.engine = MarketplaceEngine(config=cfg)
        self.host_app = FastAPI(title="JARVIS OS Host")
        mount_module(self.host_app, engine=self.engine, include_root_ui=False)
        self.client = TestClient(self.host_app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_host_app_state_and_route_mounting(self) -> None:
        self.assertIs(self.host_app.state.marketplace, self.engine)
        status = self.client.get("/api/v1/marketplace/status")
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json()["adapter"], "local_plugin_registry_engine")
        self.assertFalse(status.json()["simulated"])

    def test_end_to_end_search_and_audit_listing(self) -> None:
        pub = self.client.post(
            "/api/v1/marketplace/packages",
            json={"slug": "git-helper", "name": "Git Helper Plugin", "version": "2.0.0", "permissions": ["read_files"]},
        ).json()
        self.client.post(f"/api/v1/marketplace/packages/{pub['package_id']}/install", json={"enabled": True})

        found = self.client.get("/api/v1/marketplace/packages?q=git")
        self.assertEqual(found.status_code, 200)
        self.assertEqual(found.json()["count"], 1)

        audit = self.client.get("/api/v1/marketplace/audit")
        self.assertEqual(audit.status_code, 200)
        self.assertEqual(audit.json()["count"], 2)


if __name__ == "__main__":
    unittest.main()
