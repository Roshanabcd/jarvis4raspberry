"""Runnable CLI demo for JARVIS Module 38 — Plugin & Skills Marketplace."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import MarketplaceConfig
from backend.services.marketplace_engine import MarketplaceEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cfg = MarketplaceConfig(db_path=str(Path(tmp) / "demo_marketplace.db"))
        engine = MarketplaceEngine(config=cfg)
        pkg = engine.publish_package(
            {
                "slug": "pi5-thermal-guard",
                "name": "Pi 5 Thermal Guard",
                "version": "1.0.0",
                "kind": "plugin",
                "author": "Roshan Sharma",
                "description": "Monitors Raspberry Pi 5 thermal zones and alerts.",
                "permissions": ["telemetry_read", "notifications"],
                "manifest_payload": '{"entry":"thermal_guard.py"}',
            }
        )
        installed = engine.install_package(pkg["package_id"], expected_sha256=pkg["sha256"], enabled=True)
        disabled = engine.toggle_package(pkg["package_id"], enabled=False)
        print(
            json.dumps(
                {
                    "simulated": engine.is_simulated,
                    "package_id": pkg["package_id"],
                    "installed": installed["installed"],
                    "enabled_after_toggle": disabled["enabled"],
                    "audit_events": len(engine.db.list_audit()),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
