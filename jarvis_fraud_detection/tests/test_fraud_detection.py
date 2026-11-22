"""End-to-end tests for JARVIS Fraud Detection System."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from jarvis_fraud_detection.app import create_app
from jarvis_fraud_detection.config import FraudDetectionConfig


class TestFraudDetection(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self._tmpdir.name) / "test_fraud.db"
        cfg = FraudDetectionConfig(db_path=db_path)
        self.client = TestClient(create_app(config=cfg))

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_health_and_ui(self) -> None:
        ui = self.client.get("/fraud-detection")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("Fraud Detection System", ui.text)

        health = self.client.get("/api/fraud-detection/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["total_events"], 0)

    def test_transaction_zscore_geo_device_anomaly_and_alert_triage(self) -> None:
        # Establish normal spending baseline for actor_1
        baseline = [
            {"stream_type": "transaction", "actor_id": "actor_1", "action": "card_purchase", "amount": 45.0, "geo_country": "NP", "device_id": "dev_a"},
            {"stream_type": "transaction", "actor_id": "actor_1", "action": "card_purchase", "amount": 52.0, "geo_country": "NP", "device_id": "dev_a"},
            {"stream_type": "transaction", "actor_id": "actor_1", "action": "card_purchase", "amount": 48.0, "geo_country": "NP", "device_id": "dev_a"},
        ]
        batch = self.client.post("/api/fraud-detection/events/batch", json={"events": baseline})
        self.assertEqual(batch.status_code, 200)
        self.assertEqual(batch.json()["alerts_created"], 0)

        # Sudden high-value transfer from unseen country and unseen device -> critical / block
        spike = self.client.post(
            "/api/fraud-detection/events",
            json={
                "stream_type": "transaction",
                "actor_id": "actor_1",
                "action": "wire_transfer",
                "amount": 9500.0,
                "geo_country": "RU",
                "device_id": "dev_unknown_99",
            },
        )
        self.assertEqual(spike.status_code, 200)
        s_data = spike.json()
        self.assertEqual(s_data["decision"], "block")
        self.assertEqual(s_data["severity"], "critical")
        self.assertIsNotNone(s_data["alert_id"])
        codes = {sig["code"] for sig in s_data["signals"]}
        self.assertIn("AMOUNT_ZSCORE_SPIKE", codes)
        self.assertIn("NEW_GEO_LOCATION", codes)

        # Triage the alert to resolved
        patch = self.client.patch(
            f"/api/fraud-detection/alerts/{s_data['alert_id']}",
            json={"status": "resolved", "analyst_note": "Confirmed fraudulent wire blocked."},
        )
        self.assertEqual(patch.status_code, 200)
        self.assertEqual(patch.json()["status"], "resolved")

    def test_auth_brute_force_and_critical_audit_entry(self) -> None:
        # 3 failed logins followed by 4th failed login -> BRUTE_FORCE_BURST
        for _ in range(3):
            self.client.post(
                "/api/fraud-detection/events",
                json={"stream_type": "auth_log", "actor_id": "admin_pi", "action": "ssh_login", "status": "failed", "ip_address": "10.0.0.5"},
            )
        fourth = self.client.post(
            "/api/fraud-detection/events",
            json={"stream_type": "auth_log", "actor_id": "admin_pi", "action": "ssh_login", "status": "failed", "ip_address": "10.0.0.99", "geo_country": "DE"},
        )
        self.assertEqual(fourth.status_code, 200)
        self.assertGreaterEqual(fourth.json()["risk_score"], 40.0)
        self.assertIn("BRUTE_FORCE_BURST", {s["code"] for s in fourth.json()["signals"]})

        # Critical audit action (disable_mfa)
        audit = self.client.post(
            "/api/fraud-detection/events",
            json={"stream_type": "audit_entry", "actor_id": "admin_pi", "action": "disable_mfa", "status": "denied"},
        )
        self.assertEqual(audit.status_code, 200)
        self.assertIn("CRITICAL_AUDIT_ACTION", {s["code"] for s in audit.json()["signals"]})
        self.assertIsNotNone(audit.json()["alert_id"])

        summary = self.client.get("/api/fraud-detection/summary")
        self.assertEqual(summary.status_code, 200)
        self.assertGreaterEqual(summary.json()["total_events"], 5)


if __name__ == "__main__":
    unittest.main()
