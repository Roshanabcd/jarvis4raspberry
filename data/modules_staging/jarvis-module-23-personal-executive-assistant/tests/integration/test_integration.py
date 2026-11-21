"""Integration tests for mounting Module 23 into an existing JARVIS OS FastAPI host."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.config import ExecutiveAssistantConfig
from backend.app.main import mount_module
from backend.services.executive_engine import PersonalExecutiveEngine


class TestJarvisHostIntegration(unittest.TestCase):
    def test_additive_mount_preserves_host_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            host = FastAPI(title="Simulated JARVIS OS Host")

            @host.get("/api/core/ping")
            async def core_ping():
                return {"core": "alive"}

            cfg = ExecutiveAssistantConfig(db_path=str(Path(tmp) / "host_m23.db"))
            svc = PersonalExecutiveEngine(config=cfg)
            mount_module(host, engine=svc)

            client = TestClient(host)
            self.assertEqual(client.get("/api/core/ping").json(), {"core": "alive"})
            self.assertEqual(client.get("/api/v1/executive-assistant/health").status_code, 200)
            self.assertEqual(client.get("/executive-assistant").status_code, 200)
            svc.db.close()


if __name__ == "__main__":
    unittest.main()
