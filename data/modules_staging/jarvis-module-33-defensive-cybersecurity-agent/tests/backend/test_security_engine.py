"""Unit tests for DefensiveSecurityEngine (JARVIS Module 33)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.app.config import CyberSecurityConfig
from backend.services.security_engine import CyberSecurityError, DefensiveSecurityEngine


class TestDefensiveSecurityEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.scan_root = Path(self._tmp.name) / "scan_root"
        self.scan_root.mkdir()
        cfg = CyberSecurityConfig(
            db_path=str(Path(self._tmp.name) / "test_m33.db"),
            scan_root=str(self.scan_root),
            brute_force_threshold=3,
        )
        self.engine = DefensiveSecurityEngine(config=cfg)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_secret_scan_redaction_and_sandbox_guard(self) -> None:
        self.assertFalse(self.engine.scanner.is_simulated)
        synthetic = "AKIA" + "9876543210ABCDEF"
        (self.scan_root / "creds.env").write_text(f"KEY={synthetic}\n", encoding="utf-8")

        scan = self.engine.run_secret_scan(".")
        self.assertEqual(scan["findings_count"], 1)
        self.assertEqual(scan["findings"][0]["rule"], "aws_access_key")
        self.assertNotIn(synthetic, scan["findings"][0]["masked_match"])
        self.assertEqual(scan["findings"][0]["masked_match"], "AKIA...CDEF")

        with self.assertRaises(CyberSecurityError) as ctx:
            self.engine.run_secret_scan("../../etc")
        self.assertEqual(ctx.exception.code, "PATH_OUTSIDE_SANDBOX")
        self.assertEqual(ctx.exception.status_code, 403)

    def test_fim_baseline_and_drift_detection(self) -> None:
        target = self.scan_root / "policy.conf"
        target.write_text("allow_root=false\n", encoding="utf-8")
        bl = self.engine.create_fim_baseline("Policy Baseline", ".")
        clean = self.engine.verify_fim_baseline(bl["baseline_id"])
        self.assertFalse(clean["drift_detected"])

        target.write_text("allow_root=true\n", encoding="utf-8")
        (self.scan_root / "unexpected.sh").write_text("#!/bin/sh\n", encoding="utf-8")
        drift = self.engine.verify_fim_baseline(bl["baseline_id"])
        self.assertTrue(drift["drift_detected"])
        self.assertEqual(drift["modified"], ["policy.conf"])
        self.assertEqual(drift["added"], ["unexpected.sh"])

    def test_log_anomaly_analysis_and_incident_resolution(self) -> None:
        lines = [
            "sshd: Failed password for admin from 198.51.100.7 port 22",
            "sshd: Failed password for admin from 198.51.100.7 port 22",
            "sshd: Failed password for admin from 198.51.100.7 port 22",
            "GET /search?q=UNION SELECT * FROM users HTTP/1.1",
        ]
        res = self.engine.analyze_logs("auth_web.log", lines)
        self.assertEqual(res["incidents_created"], 2)
        inc_id = res["incidents"][0]["incident_id"]
        resolved = self.engine.resolve_incident(inc_id, "Blocked IP in ufw")
        self.assertEqual(resolved["status"], "resolved")


if __name__ == "__main__":
    unittest.main()
