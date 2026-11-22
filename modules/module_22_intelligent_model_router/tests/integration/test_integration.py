"""Integration tests for mounting Module 22 into an existing JARVIS OS FastAPI host."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.module_22_intelligent_model_router.backend.app.config import ModelRouterConfig
from modules.module_22_intelligent_model_router.backend.app.main import mount_module
from modules.module_22_intelligent_model_router.backend.services.router_engine import IntelligentModelRouterEngine


class TestJarvisHostIntegration(unittest.TestCase):
    def test_additive_mount_preserves_host_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            host = FastAPI(title="Simulated JARVIS OS Host")

            @host.get("/api/core/ping")
            async def core_ping():
                return {"core": "alive"}

            cfg = ModelRouterConfig(db_path=str(Path(tmp) / "host_m22.db"))
            svc = IntelligentModelRouterEngine(config=cfg)
            mount_module(host, engine=svc)

            client = TestClient(host)
            self.assertEqual(client.get("/api/core/ping").json(), {"core": "alive"})
            self.assertEqual(client.get("/api/v1/model-router/health").status_code, 200)
            self.assertEqual(client.get("/model-router").status_code, 200)
            svc.db.close()


if __name__ == "__main__":
    unittest.main()
