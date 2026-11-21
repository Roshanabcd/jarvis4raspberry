"""Unit tests for FinanceEngine (JARVIS Module 34)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from modules.module_34_personal_finance_manager.backend.app.config import FinanceConfig
from modules.module_34_personal_finance_manager.backend.services.finance_engine import FinanceEngine


class TestFinanceEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = FinanceConfig(db_path=str(Path(self._tmp.name) / "test_m34.db"))
        self.engine = FinanceEngine(config=cfg)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_ledger_balances_and_overdraft_warning(self) -> None:
        self.assertFalse(self.engine.is_simulated)
        acc = self.engine.create_account(
            {"name": "Main Checking", "account_type": "checking", "currency": "USD", "opening_balance": 100.0}
        )
        res = self.engine.record_transaction(
            {
                "account_id": acc["account_id"],
                "tx_type": "expense",
                "amount": 150.0,
                "category": "Hardware",
                "tx_date": "2026-11-12",
            }
        )
        self.assertEqual(res["account_balance"], -50.0)
        self.assertTrue(res["overdraft_warning"])

    def test_budget_utilization_and_exceeded_status(self) -> None:
        acc = self.engine.create_account({"name": "Wallet", "account_type": "cash", "opening_balance": 500.0})
        self.engine.upsert_budget({"month": "2026-11", "category": "Food", "limit_amount": 200.0})
        self.engine.record_transaction(
            {
                "account_id": acc["account_id"],
                "tx_type": "expense",
                "amount": 220.0,
                "category": "Food",
                "tx_date": "2026-11-14",
            }
        )
        st = self.engine.get_budget_status("2026-11")
        self.assertEqual(st["budgets"][0]["status"], "exceeded")
        self.assertEqual(st["budgets"][0]["utilization_pct"], 110.0)

    def test_goals_summary_and_csv_export(self) -> None:
        acc = self.engine.create_account({"name": "Savings", "account_type": "savings", "opening_balance": 1000.0})
        self.engine.record_transaction(
            {"account_id": acc["account_id"], "tx_type": "income", "amount": 1000.0, "category": "Salary", "tx_date": "2026-11-01"}
        )
        self.engine.record_transaction(
            {"account_id": acc["account_id"], "tx_type": "expense", "amount": 250.0, "category": "Utilities", "tx_date": "2026-11-05"}
        )
        summary = self.engine.get_summary("2026-11")
        self.assertEqual(summary["net_worth"], 1750.0)
        self.assertEqual(summary["savings_rate_pct"], 75.0)

        goal = self.engine.create_goal({"name": "Emergency Fund", "target_amount": 500.0, "current_amount": 250.0})
        goal = self.engine.contribute_goal(goal["goal_id"], 250.0)
        self.assertTrue(goal["completed"])
        self.assertEqual(goal["progress_pct"], 100.0)

        csv_out = self.engine.export_transactions_csv("2026-11")
        self.assertIn("Utilities", csv_out)
        self.assertEqual(len(csv_out.splitlines()), 3)


if __name__ == "__main__":
    unittest.main()
