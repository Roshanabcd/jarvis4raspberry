"""Runnable CLI demo for JARVIS Module 37 — Cross-Device Control Center."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import DeviceMeshConfig
from backend.services.device_mesh_engine import DeviceMeshEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cfg = DeviceMeshConfig(db_path=str(Path(tmp) / "demo_devices.db"))
        engine = DeviceMeshEngine(config=cfg)
        pi5 = engine.register_device(
            {
                "name": "Roshan-Pi5",
                "device_type": "raspberry_pi",
                "platform": "linux",
                "capabilities": ["clipboard", "media", "notifications"],
                "battery_pct": 100,
                "online": True,
            }
        )
        cmd = engine.dispatch_command(pi5["device_id"], "notifications", "toast", {"text": "Mesh Online"})
        clip = engine.sync_clipboard(pi5["device_id"], "https://jarvis.local:8137/devices")
        print(
            json.dumps(
                {
                    "simulated": engine.is_simulated,
                    "device_id": pi5["device_id"],
                    "command_message": cmd["result"]["message"],
                    "clipboard_sha256_prefix": clip["sha256"][:12],
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
