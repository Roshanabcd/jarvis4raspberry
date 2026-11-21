"""Tests 9-14: Registry Persistence, Enable/Disable, Real Health Monitor, SDK, and Event Bus."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import httpx

from modules.module_42_unified_extension_manager.backend.app.config import ExtensionManagerConfig
from modules.module_42_unified_extension_manager.backend.models.database import ExtensionRegistryDB
from modules.module_42_unified_extension_manager.backend.services.health_monitor import ModuleHealthMonitor
from modules.module_42_unified_extension_manager.sample_extension.extension import SampleDiagnosticsExtension
from modules.module_42_unified_extension_manager.sdk.jarvis_sdk import (
    ApprovalRequest,
    AuthContext,
    EventBus,
    HealthStatus,
    JarvisEvent,
    ReferenceHostAdapter,
)


class TestRegistryHealthSdkAndEvents(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self._tmp.name) / "registry.db")
        self.db = ExtensionRegistryDB(self.db_path)

    def tearDown(self) -> None:
        self.db.close()
        self._tmp.cleanup()

    def test_09_and_10_registry_persistence_and_enable_disable(self) -> None:
        self.db.upsert_module(
            {
                "module_id": "jarvis-module-18",
                "name": "Multi-Agent Orchestrator",
                "version": "1.0.0",
                "category": "core_orchestration",
                "enabled": False,
                "required_permissions": ["orchestrator.tasks.create"],
            }
        )
        toggled = self.db.set_enabled("jarvis-module-18", True)
        self.assertTrue(toggled["enabled"])
        self.assertEqual(toggled["health_status"], HealthStatus.NOT_VERIFIED.value)

        # Reopen SQLite DB to prove persistence
        self.db.close()
        self.db = ExtensionRegistryDB(self.db_path)
        reloaded = self.db.get_module("jarvis-module-18")
        self.assertIsNotNone(reloaded)
        self.assertTrue(reloaded["enabled"])

        disabled = self.db.set_enabled("jarvis-module-18", False)
        self.assertFalse(disabled["enabled"])
        self.assertEqual(disabled["health_status"], HealthStatus.DISABLED.value)

    async def test_11_health_checks_all_states(self) -> None:
        monitor = ModuleHealthMonitor(self.db, ExtensionManagerConfig(db_path=self.db_path))

        # Disabled module -> disabled
        self.db.upsert_module({"module_id": "m-disabled", "name": "Disabled", "version": "1.0.0", "enabled": False})
        r_dis = await monitor.probe_module("m-disabled")
        self.assertEqual(r_dis.status, HealthStatus.DISABLED)

        # Enabled without endpoint -> not_configured (never healthy from existence alone!)
        self.db.upsert_module({"module_id": "m-noconf", "name": "NoConf", "version": "1.0.0", "enabled": True})
        r_nc = await monitor.probe_module("m-noconf")
        self.assertEqual(r_nc.status, HealthStatus.NOT_CONFIGURED)

        # Mock HTTP responses for healthy, degraded, unavailable
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/healthy":
                return httpx.Response(200, json={"status": "ok"})
            if request.url.path == "/degraded":
                return httpx.Response(200, json={"status": "degraded"})
            return httpx.Response(503, json={"status": "down"})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            for mid, path, expected in [
                ("m-ok", "http://local.test/healthy", HealthStatus.HEALTHY),
                ("m-deg", "http://local.test/degraded", HealthStatus.DEGRADED),
                ("m-down", "http://local.test/down", HealthStatus.UNAVAILABLE),
            ]:
                self.db.upsert_module({"module_id": mid, "name": mid, "version": "1.0.0", "enabled": True, "health_endpoint": path})
                res = await monitor.probe_module(mid, client=client)
                self.assertEqual(res.status, expected)

    async def test_12_sdk_api_behavior_and_sample_extension(self) -> None:
        host = ReferenceHostAdapter()
        sample = SampleDiagnosticsExtension(host)
        discovered = host.discover_modules(category="diagnostics")
        self.assertEqual(len(discovered), 1)
        self.assertEqual(discovered[0].module_id, sample.MODULE_ID)

        # Auth decision checks
        denied = host.check_authorization(AuthContext(subject="guest", authenticated=False), "diagnostics.read")
        self.assertFalse(denied.allowed)
        allowed = host.check_authorization(
            AuthContext(subject="roshan", authenticated=True, scopes=["diagnostics.read"]), "diagnostics.read"
        )
        self.assertTrue(allowed.allowed)

        # Approval request contract
        apr = host.request_approval(ApprovalRequest(module_id=sample.MODULE_ID, action="install", summary="Install sample"))
        self.assertEqual(apr.status, "pending")
        self.assertEqual(host.check_module_health(sample.MODULE_ID).status, HealthStatus.HEALTHY)

    async def test_13_and_14_event_delivery_and_failed_delivery_retries(self) -> None:
        bus = EventBus(max_retries=2, retry_delay_seconds=0.005, persist_fn=self.db.persist_event)
        received = []
        attempts = {"flaky": 0, "broken": 0}

        async def good_handler(evt: JarvisEvent) -> None:
            received.append(evt.event_id)

        async def flaky_handler(evt: JarvisEvent) -> None:
            attempts["flaky"] += 1
            if attempts["flaky"] < 2:
                raise RuntimeError("Transient error")

        async def broken_handler(evt: JarvisEvent) -> None:
            attempts["broken"] += 1
            raise RuntimeError("Permanent failure")

        bus.subscribe("module.updated", good_handler)
        bus.subscribe("module.updated", flaky_handler)
        bus.subscribe("module.updated", broken_handler)

        evt = JarvisEvent(event_type="module.updated", source_module="module-42", payload={"id": "m18"})
        report = await bus.publish(evt)

        self.assertEqual(report.delivered_count, 2)
        self.assertEqual(report.failed_count, 1)
        self.assertEqual(attempts["flaky"], 2)
        self.assertEqual(attempts["broken"], 3)  # 1 initial + 2 retries
        self.assertEqual(len(bus.get_dead_letters()), 1)
        self.assertEqual(len(self.db.list_events()), 1)


if __name__ == "__main__":
    unittest.main()
