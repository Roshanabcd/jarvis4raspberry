"""Runnable CLI demo for JARVIS Module 34 — Personal Finance Manager."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import FinanceConfig
from backend.services.finance_engine import FinanceEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cfg = FinanceConfig(db_path=str(Path(tmp) / "demo_finance.db"))
        engine = FinanceEngine(config=cfg)

        checking = engine.create_account(
            {"name": "Primary Checking", "account_type": "checking", "currency": "USD", "opening_balance": 1500.0}
        )
        engine.upsert_budget({"month": "2026-11", "category": "Groceries", "limit_amount": 300.0})
        engine.record_transaction(
            {
                "account_id": checking["account_id"],
                "tx_type": "income",
                "amount": 2500.0,
                "category": "Salary",
                "merchant": "Employer",
                "tx_date": "2026-11-01",
            }
        )
        engine.record_transaction(
            {
                "account_id": checking["account_id"],
                "tx_type": "expense",
                "amount": 260.0,
                "category": "Groceries",
                "merchant": "Local Market",
                "tx_date": "2026-11-10",
            }
        )
        goal = engine.create_goal({"name": "Pi 5 Cluster Upgrade", "target_amount": 500.0, "current_amount": 150.0})
        goal = engine.contribute_goal(goal["goal_id"], 100.0)

        print(
            json.dumps(
                {
                    "simulated": engine.is_simulated,
                    "summary": engine.get_summary("2026-11"),
                    "goal_progress_pct": goal["progress_pct"],
                    "csv_rows": len(engine.export_transactions_csv("2026-11").splitlines()),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
