"""Runnable CLI demo for JARVIS Module 41 — Universal Notification Center."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.module_41_universal_notification_center.backend.app.config import NotificationConfig
from modules.module_41_universal_notification_center.backend.services.notification_engine import NotificationEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cfg = NotificationConfig(db_path=str(Path(tmp) / "demo_notifications.db"))
        engine = NotificationEngine(config=cfg)
        engine.update_preferences(dnd_enabled=True, allow_critical_during_dnd=True, enabled_channels=["hud", "desktop"])
        low = engine.send_notification(
            {
                "source_module": "module-24-email",
                "title": "Newsletter",
                "message": "Weekly digest",
                "priority": "low",
                "channels": ["hud"],
            }
        )
        crit = engine.send_notification(
            {
                "source_module": "module-33-cybersecurity",
                "title": "Firewall Alert",
                "message": "Blocked unauthorized port scan",
                "priority": "critical",
                "channels": ["hud", "desktop"],
                "dedupe_key": "fw-scan-1",
            }
        )
        dup = engine.send_notification(
            {
                "source_module": "module-33-cybersecurity",
                "title": "Firewall Alert",
                "message": "Blocked unauthorized port scan",
                "priority": "critical",
                "channels": ["hud"],
                "dedupe_key": "fw-scan-1",
            }
        )
        print(
            json.dumps(
                {
                    "simulated": engine.is_simulated,
                    "low_during_dnd_status": low["status"],
                    "critical_during_dnd_status": crit["status"],
                    "deduplicated": dup["deduplicated"],
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
