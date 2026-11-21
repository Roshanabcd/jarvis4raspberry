"""Runnable CLI demo for JARVIS Module 42 using synthetic safe & malicious ZIP fixtures."""

from __future__ import annotations

import asyncio
import json
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.config import ExtensionManagerConfig
from backend.services.extension_manager import ExtensionManager
from sample_extension.extension import SampleDiagnosticsExtension
from sdk.jarvis_sdk import JarvisEvent, ReferenceHostAdapter


def _build_synthetic_archives(folder: Path) -> None:
    # 1. Valid synthetic module archive
    with zipfile.ZipFile(folder / "synthetic_mod_alpha.zip", "w") as zf:
        zf.writestr(
            "mod_alpha/manifest.json",
            json.dumps(
                {
                    "module_id": "jarvis-synthetic-alpha",
                    "name": "Synthetic Alpha Module",
                    "version": "1.0.0",
                    "category": "automation",
                    "compatible_api_version": "1.0.0",
                    "entrypoints": {"api_prefix": "/api/v1/alpha", "default_port": 8201},
                    "required_permissions": ["alpha.run"],
                    "dependencies": {"jarvis_modules": []},
                }
            ),
        )
        zf.writestr("mod_alpha/README.md", "# Synthetic Alpha")
        zf.writestr("mod_alpha/requirements.txt", "fastapi>=0.92.0\n")
        zf.writestr("mod_alpha/backend/app/main.py", "# entry\n")

    # 2. Malicious path traversal archive (rejected safely without extraction)
    with zipfile.ZipFile(folder / "malicious_traversal.zip", "w") as zf:
        zf.writestr("../../etc/evil.txt", "blocked")


async def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        archives_dir = tmp_path / "archives"
        archives_dir.mkdir()
        _build_synthetic_archives(archives_dir)

        cfg = ExtensionManagerConfig(db_path=str(tmp_path / "m42_demo.db"))
        mgr = ExtensionManager(config=cfg)
        scan_report = mgr.scan_folder(str(archives_dir), register_discovered=True, target_arch="arm64")
        plan = mgr.build_install_plan(["jarvis-synthetic-alpha"])

        # Demonstrate SDK + Sample Extension + EventBus
        host = ReferenceHostAdapter()
        sample = SampleDiagnosticsExtension(host)
        delivery = await host.publish_event(JarvisEvent(event_type="extension.ping", source_module="demo-cli", payload={"ok": True}))

        print(
            json.dumps(
                {
                    "simulated": mgr.is_simulated,
                    "archives_scanned": scan_report["archive_count"],
                    "valid_archives": scan_report["valid_count"],
                    "rejected_archives": scan_report["rejected_count"],
                    "plan_dry_run": plan["dry_run"],
                    "plan_ready_for_approval": plan["ready_for_approval"],
                    "sample_extension_health": host.check_module_health(sample.MODULE_ID).status.value,
                    "sdk_event_delivered": delivery["delivered_count"],
                },
                indent=2,
            )
        )
        mgr.db.close()


if __name__ == "__main__":
    asyncio.run(main())
