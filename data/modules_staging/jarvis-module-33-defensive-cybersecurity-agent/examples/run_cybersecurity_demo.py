"""Runnable CLI demo for JARVIS Module 33 — Defensive Cybersecurity Agent."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import CyberSecurityConfig
from backend.services.security_engine import DefensiveSecurityEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        scan_root = Path(tmp) / "workspace"
        scan_root.mkdir()
        sample_cfg = scan_root / "app.env"
        # Dynamically construct synthetic test token so source tree has zero hardcoded secrets
        synthetic_key = "AKIA" + "0123456789ABCDEF"
        sample_cfg.write_text(f"AWS_ACCESS_KEY_ID={synthetic_key}\n", encoding="utf-8")

        cfg = CyberSecurityConfig(db_path=str(Path(tmp) / "demo_sec.db"), scan_root=str(scan_root))
        engine = DefensiveSecurityEngine(config=cfg)

        # 1. Secret scan with automatic masking
        scan = engine.run_secret_scan(".")

        # 2. FIM baseline & drift detection
        bl = engine.create_fim_baseline("Config Baseline", ".")
        sample_cfg.write_text("AWS_ACCESS_KEY_ID=REDACTED\n", encoding="utf-8")
        drift = engine.verify_fim_baseline(bl["baseline_id"])

        # 3. Auth log anomaly analysis
        log_res = engine.analyze_logs(
            "auth.log",
            [
                "Nov 20 10:01:01 pi5 sshd[100]: Failed password for root from 203.0.113.55 port 44122 ssh2",
                "Nov 20 10:01:02 pi5 sshd[101]: Failed password for root from 203.0.113.55 port 44123 ssh2",
                "Nov 20 10:01:03 pi5 sshd[102]: Failed password for root from 203.0.113.55 port 44124 ssh2",
            ],
        )

        print(
            json.dumps(
                {
                    "simulated": engine.scanner.is_simulated,
                    "scan_findings_count": scan["findings_count"],
                    "masked_match": scan["findings"][0]["masked_match"],
                    "fim_drift_detected": drift["drift_detected"],
                    "fim_modified": drift["modified"],
                    "log_incidents_created": log_res["incidents_created"],
                    "status": engine.get_status(),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
