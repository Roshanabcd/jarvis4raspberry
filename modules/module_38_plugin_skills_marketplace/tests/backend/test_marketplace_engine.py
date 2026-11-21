"""Unit tests for Module 38 MarketplaceEngine (SemVer, checksum, permission allowlist, lifecycle)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from modules.module_38_plugin_skills_marketplace.backend.app.config import MarketplaceConfig
from modules.module_38_plugin_skills_marketplace.backend.services.marketplace_engine import MarketplaceEngine, MarketplaceError


class TestMarketplaceEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = MarketplaceConfig(db_path=str(Path(self._tmp.name) / "marketplace.db"))
        self.engine = MarketplaceEngine(config=cfg)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_publish_install_toggle_uninstall_and_audit(self) -> None:
        pkg = self.engine.publish_package(
            {
                "slug": "briefing-helper",
                "name": "Briefing Helper",
                "version": "1.2.3",
                "kind": "skill",
                "permissions": ["calendar_read", "notifications"],
                "manifest_payload": '{"entry":"brief.py"}',
            }
        )
        self.assertEqual(len(pkg["sha256"]), 64)
        self.assertFalse(pkg["installed"])

        inst = self.engine.install_package(pkg["package_id"], expected_sha256=pkg["sha256"], enabled=True)
        self.assertTrue(inst["installed"])
        self.assertTrue(inst["enabled"])

        dis = self.engine.toggle_package(pkg["package_id"], enabled=False)
        self.assertFalse(dis["enabled"])

        uninst = self.engine.uninstall_package(pkg["package_id"])
        self.assertFalse(uninst["installed"])
        self.assertEqual(len(self.engine.db.list_audit()), 4)
        self.assertFalse(self.engine.get_status()["simulated"])

    def test_rejects_bad_semver_disallowed_perms_and_duplicates(self) -> None:
        with self.assertRaises(MarketplaceError) as e1:
            self.engine.publish_package({"slug": "bad-ver", "name": "Bad", "version": "1.0"})
        self.assertEqual(e1.exception.code, "INVALID_SEMVER")

        with self.assertRaises(MarketplaceError) as e2:
            self.engine.publish_package(
                {"slug": "bad-perm", "name": "Bad", "version": "1.0.0", "permissions": ["root_exec"]}
            )
        self.assertEqual(e2.exception.code, "DISALLOWED_PERMISSION")

        self.engine.publish_package({"slug": "dup-pkg", "name": "Dup", "version": "1.0.0"})
        with self.assertRaises(MarketplaceError) as e3:
            self.engine.publish_package({"slug": "dup-pkg", "name": "Dup", "version": "1.0.0"})
        self.assertEqual(e3.exception.code, "PACKAGE_ALREADY_EXISTS")
        self.assertEqual(e3.exception.status_code, 409)

    def test_checksum_mismatch_rejected_on_install(self) -> None:
        pkg = self.engine.publish_package({"slug": "safe-skill", "name": "Safe", "version": "1.0.0"})
        with self.assertRaises(MarketplaceError) as err:
            self.engine.install_package(pkg["package_id"], expected_sha256="0" * 64)
        self.assertEqual(err.exception.code, "CHECKSUM_MISMATCH")
        self.assertEqual(err.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
