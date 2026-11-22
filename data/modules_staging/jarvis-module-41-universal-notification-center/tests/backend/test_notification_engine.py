"""Unit tests for Module 41 — NotificationEngine."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.app.config import NotificationConfig
from backend.services.notification_engine import NotificationEngine, NotificationError


class TestNotificationEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = NotificationConfig(db_path=str(Path(self._tmp.name) / "notifications.db"))
        self.engine = NotificationEngine(config=cfg)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_dnd_suppression_and_critical_override(self) -> None:
        self.assertFalse(self.engine.is_simulated)
        prefs = self.engine.update_preferences(
            dnd_enabled=True,
            allow_critical_during_dnd=True,
            enabled_channels=["hud", "desktop", "voice"],
        )
        self.assertTrue(prefs["dnd_enabled"])

        suppressed = self.engine.send_notification(
            {
                "source_module": "module-32-system-health",
                "title": "Routine Metric Update",
                "message": "CPU temperature nominal.",
                "priority": "normal",
                "channels": ["hud", "desktop"],
            }
        )
        self.assertEqual(suppressed["status"], "suppressed")
        self.assertEqual(suppressed["delivered_channels"], [])
        self.assertFalse(suppressed["deduplicated"])

        critical = self.engine.send_notification(
            {
                "source_module": "module-33-cybersecurity",
                "title": "SSH Brute Force Detected",
                "message": "Blocked repeated login attempts.",
                "priority": "critical",
                "channels": ["hud", "voice", "email"],
            }
        )
        self.assertEqual(critical["status"], "unread")
        self.assertEqual(critical["delivered_channels"], ["hud", "voice"])

    def test_dedupe_key_idempotency_and_lifecycle(self) -> None:
        first = self.engine.send_notification(
            {
                "source_module": "module-39-backup",
                "title": "Nightly Snapshot Complete",
                "message": "Snapshot archived with SHA-256 verification.",
                "priority": "high",
                "channels": ["hud"],
                "dedupe_key": "backup-2026-nightly",
            }
        )
        self.assertFalse(first["deduplicated"])

        second = self.engine.send_notification(
            {
                "source_module": "module-39-backup",
                "title": "Nightly Snapshot Complete",
                "message": "Duplicate trigger.",
                "priority": "high",
                "channels": ["hud"],
                "dedupe_key": "backup-2026-nightly",
            }
        )
        self.assertTrue(second["deduplicated"])
        self.assertEqual(second["notification_id"], first["notification_id"])

        acked = self.engine.acknowledge(first["notification_id"])
        self.assertEqual(acked["status"], "acknowledged")
        dismissed = self.engine.dismiss(first["notification_id"])
        self.assertEqual(dismissed["status"], "dismissed")

    def test_validation_and_missing_id_errors(self) -> None:
        with self.assertRaises(NotificationError) as ctx_prio:
            self.engine.send_notification(
                {
                    "source_module": "module-41",
                    "title": "Bad Priority",
                    "message": "Invalid priority level.",
                    "priority": "urgent",
                    "channels": ["hud"],
                }
            )
        self.assertEqual(ctx_prio.exception.code, "INVALID_PRIORITY")
        self.assertEqual(ctx_prio.exception.status_code, 422)

        with self.assertRaises(NotificationError) as ctx_chan:
            self.engine.send_notification(
                {
                    "source_module": "module-41",
                    "title": "Bad Channel",
                    "message": "Unsupported channel.",
                    "priority": "normal",
                    "channels": ["pager"],
                }
            )
        self.assertEqual(ctx_chan.exception.code, "UNSUPPORTED_CHANNEL")
        self.assertEqual(ctx_chan.exception.status_code, 422)

        with self.assertRaises(NotificationError) as ctx_missing:
            self.engine.acknowledge("ntf_nonexistent")
        self.assertEqual(ctx_missing.exception.code, "NOTIFICATION_NOT_FOUND")
        self.assertEqual(ctx_missing.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
