"""FastAPI REST & WebSocket tests for JARVIS Module 34 — Personal Finance Manager."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import FinanceConfig
from backend.app.main import create_app


class TestFinanceAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = FinanceConfig(db_path=str(Path(self._tmp.name) / "api_m34.db"))
        self.app = create_app(cfg)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_manifest_and_ui_route(self) -> None:
        h = self.client.get("/api/v1/finance/health")
        self.assertEqual(h.status_code, 200)
        self.assertEqual(h.json()["module_id"], "jarvis-module-34-personal-finance-manager")
        self.assertFalse(h.json()["simulated"])

        m = self.client.get("/api/v1/finance/manifest")
        self.assertEqual(m.status_code, 200)
        self.assertEqual(m.json()["default_port"], 8134)

        ui = self.client.get("/finance")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("PERSONAL FINANCE MANAGER", ui.text)

    def test_account_tx_budget_and_csv_endpoints(self) -> None:
        acc = self.client.post(
            "/api/v1/finance/accounts",
            json={"name": "Checking", "account_type": "checking", "currency": "USD", "opening_balance": 500.0},
        )
        self.assertEqual(acc.status_code, 201)
        acc_id = acc.json()["account_id"]

        b = self.client.post(
            "/api/v1/finance/budgets",
            json={"month": "2026-11", "category": "Coffee", "limit_amount": 50.0},
        )
        self.assertEqual(b.status_code, 201)

        tx = self.client.post(
            "/api/v1/finance/transactions",
            json={"account_id": acc_id, "tx_type": "expense", "amount": 45.0, "category": "Coffee", "tx_date": "2026-11-15"},
        )
        self.assertEqual(tx.status_code, 201)
        self.assertEqual(tx.json()["account_balance"], 455.0)

        bs = self.client.get("/api/v1/finance/budgets/status?month=2026-11")
        self.assertEqual(bs.status_code, 200)
        self.assertEqual(bs.json()["budgets"][0]["status"], "warning")

        csv_res = self.client.get("/api/v1/finance/transactions/export.csv?month=2026-11")
        self.assertEqual(csv_res.status_code, 200)
        self.assertIn("Coffee", csv_res.text)

    def test_websocket_updates_stream(self) -> None:
        with self.client.websocket_connect("/api/v1/finance/ws/updates") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")
            self.assertIn("status", msg)


if __name__ == "__main__":
    unittest.main()
