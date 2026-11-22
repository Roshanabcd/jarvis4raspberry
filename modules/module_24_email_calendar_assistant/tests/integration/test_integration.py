"""Integration tests for mounting Module 24 into an existing JARVIS OS FastAPI host."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.module_24_email_calendar_assistant.backend.app.config import EmailCalendarConfig
from modules.module_24_email_calendar_assistant.backend.app.main import mount_module
from modules.module_24_email_calendar_assistant.backend.services.email_calendar_engine import EmailCalendarEngine


class TestJarvisHostIntegration(unittest.TestCase):
    def test_additive_mount_preserves_host_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            host = FastAPI(title="Simulated JARVIS OS Host")

            @host.get("/api/core/ping")
            async def core_ping():
                return {"core": "alive"}

            cfg = EmailCalendarConfig(db_path=str(Path(tmp) / "host_m24.db"))
            svc = EmailCalendarEngine(config=cfg)
            mount_module(host, engine=svc)

            client = TestClient(host)
            self.assertEqual(client.get("/api/core/ping").json(), {"core": "alive"})
            self.assertEqual(client.get("/api/v1/email-calendar/health").status_code, 200)
            self.assertEqual(client.get("/email-calendar").status_code, 200)
            svc.db.close()


if __name__ == "__main__":
    unittest.main()
