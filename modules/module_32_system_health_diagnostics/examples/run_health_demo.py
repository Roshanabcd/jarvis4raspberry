"""Runnable CLI demo for JARVIS Module 32 — System Health & Diagnostics."""

from __future__ import annotations

import json
import socket
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.module_32_system_health_diagnostics.backend.app.config import SystemHealthConfig
from modules.module_32_system_health_diagnostics.backend.services.health_engine import SystemHealthEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cfg = SystemHealthConfig(db_path=str(Path(tmp) / "demo_health.db"))
        engine = SystemHealthEngine(config=cfg)

        # Open an ephemeral localhost TCP listener to verify real TCP probing
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        port = srv.getsockname()[1]

        try:
            engine.register_service({"name": "Demo Ephemeral Listener", "host": "127.0.0.1", "port": port})
            engine.create_rule(
                {"name": "Any Disk Usage Info", "metric_key": "disk_used_pct", "operator": ">=", "threshold": 0.0, "severity": "warning"}
            )
            diag = engine.run_diagnostics()
            print(
                json.dumps(
                    {
                        "simulated": engine.probe.is_simulated,
                        "health_score": diag["health_score"],
                        "hostname": diag["summary"]["metrics"]["hostname"],
                        "disk_used_pct": diag["summary"]["metrics"]["disk_used_pct"],
                        "memory_used_pct": diag["summary"]["metrics"]["memory_used_pct"],
                        "services": diag["summary"]["services"],
                        "open_alerts_count": diag["summary"]["open_alerts_count"],
                    },
                    indent=2,
                )
            )
        finally:
            srv.close()


if __name__ == "__main__":
    main()
