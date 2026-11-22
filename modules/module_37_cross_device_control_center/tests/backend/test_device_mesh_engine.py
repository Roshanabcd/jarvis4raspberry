"""Unit tests for Module 37 DeviceMeshEngine (registry, capability guard, offline check, clipboard)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from modules.module_37_cross_device_control_center.backend.app.config import DeviceMeshConfig
from modules.module_37_cross_device_control_center.backend.services.device_mesh_engine import DeviceMeshEngine, DeviceMeshError


class TestDeviceMeshEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = DeviceMeshConfig(db_path=str(Path(self._tmp.name) / "devices.db"))
        self.engine = DeviceMeshEngine(config=cfg)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_register_heartbeat_and_capability_guarded_command(self) -> None:
        dev = self.engine.register_device(
            {
                "name": "Pixel-9",
                "device_type": "phone",
                "platform": "android",
                "capabilities": ["notifications", "clipboard"],
                "battery_pct": 85,
                "online": True,
            }
        )
        cmd = self.engine.dispatch_command(dev["device_id"], "notifications", "toast", {"msg": "Hi"})
        self.assertEqual(cmd["status"], "executed")
        self.assertTrue(cmd["simulated"])
        self.assertIn("[SIMULATED]", cmd["result"]["message"])

        with self.assertRaises(DeviceMeshError) as cap_err:
            self.engine.dispatch_command(dev["device_id"], "lock", "lock_screen", {})
        self.assertEqual(cap_err.exception.code, "CAPABILITY_NOT_SUPPORTED")
        self.assertEqual(cap_err.exception.status_code, 422)

        updated = self.engine.heartbeat(dev["device_id"], online=False, battery_pct=80)
        self.assertFalse(updated["online"])
        self.assertEqual(updated["battery_pct"], 80)

        with self.assertRaises(DeviceMeshError) as off_err:
            self.engine.dispatch_command(dev["device_id"], "notifications", "toast", {})
        self.assertEqual(off_err.exception.code, "DEVICE_OFFLINE")
        self.assertEqual(off_err.exception.status_code, 409)

    def test_rejects_unsupported_capability_on_register(self) -> None:
        with self.assertRaises(DeviceMeshError) as err:
            self.engine.register_device({"name": "BadNode", "capabilities": ["raw_root_shell"]})
        self.assertEqual(err.exception.code, "UNSUPPORTED_CAPABILITY")
        self.assertEqual(err.exception.status_code, 422)

    def test_clipboard_sync_enforces_capability_and_hashes_content(self) -> None:
        dev = self.engine.register_device({"name": "Pi5", "capabilities": ["clipboard"]})
        entry = self.engine.sync_clipboard(dev["device_id"], "JARVIS-TOKEN-TEST")
        self.assertEqual(len(entry["sha256"]), 64)
        self.assertEqual(entry["source_device_id"], dev["device_id"])

        no_clip = self.engine.register_device({"name": "Speaker", "capabilities": ["media"]})
        with self.assertRaises(DeviceMeshError) as err:
            self.engine.sync_clipboard(no_clip["device_id"], "hello")
        self.assertEqual(err.exception.code, "CAPABILITY_NOT_SUPPORTED")
        self.assertTrue(self.engine.get_status()["simulated"])


if __name__ == "__main__":
    unittest.main()
