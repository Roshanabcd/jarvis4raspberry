"""Personal Finance Manager Engine (Module 34).

Real local SQLite WAL ledger (simulated=False) with multi-account balances,
categorized transactions, monthly budget burn tracking, savings goals,
cashflow summary, and RFC 4180 CSV export.
"""

from __future__ import annotations

import csv
import io
import time
import uuid
from typing import Any, Dict, List, Optional

from modules.module_34_personal_finance_manager.backend.app.config import FinanceConfig
from modules.module_34_personal_finance_manager.backend.models.database import FinanceDB, today_iso, utc_now_iso


class FinanceError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class FinanceEngine:
    adapter_name: str = "local_sqlite_finance_ledger"
    is_simulated: bool = False

    def __init__(
        self,
        config: Optional[FinanceConfig] = None,
        db: Optional[FinanceDB] = None,
    ) -> None:
        self.config = config or FinanceConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or FinanceDB(self.config.db_path)
        self._started_at = time.monotonic()

    def create_account(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.db.create_account(
            {
                "account_id": f"acc_{uuid.uuid4().hex[:10]}",
                "name": payload["name"].strip(),
                "account_type": payload.get("account_type", "checking"),
                "currency": payload.get("currency", self.config.default_currency).upper(),
                "balance": round(float(payload.get("opening_balance", 0.0)), 2),
                "created_at": utc_now_iso(),
            }
        )

    def record_transaction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        acc = self.db.get_account(payload["account_id"])
        if not acc:
            raise FinanceError("ACCOUNT_NOT_FOUND", f"Account '{payload['account_id']}' not found.", 404)

        amount = round(float(payload["amount"]), 2)
        tx_type = payload["tx_type"]
        delta = amount if tx_type == "income" else -amount
        new_balance = round(float(acc["balance"]) + delta, 2)
        overdraft_warning = tx_type == "expense" and acc["account_type"] != "credit" and new_balance < 0

        tx = self.db.add_transaction(
            {
                "tx_id": f"tx_{uuid.uuid4().hex[:10]}",
                "account_id": acc["account_id"],
                "tx_type": tx_type,
                "amount": amount,
                "category": payload["category"].strip(),
                "merchant": payload.get("merchant", "").strip(),
                "tx_date": (payload.get("tx_date") or today_iso())[:10],
                "note": payload.get("note", "").strip(),
                "created_at": utc_now_iso(),
            }
        )
        updated_acc = self.db.update_account_balance(acc["account_id"], new_balance)
        return {
            "transaction": tx,
            "account_balance": updated_acc["balance"],
            "overdraft_warning": overdraft_warning,
        }

    def upsert_budget(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.db.upsert_budget(
            budget_id=f"bdg_{uuid.uuid4().hex[:10]}",
            month=payload["month"],
            category=payload["category"].strip(),
            limit_amount=float(payload["limit_amount"]),
        )

    def get_budget_status(self, month: str) -> Dict[str, Any]:
        budgets = self.db.list_budgets(month=month)
        txs = self.db.list_transactions(month=month)
        spent_by_cat: Dict[str, float] = {}
        for tx in txs:
            if tx["tx_type"] == "expense":
                key = tx["category"].lower()
                spent_by_cat[key] = round(spent_by_cat.get(key, 0.0) + float(tx["amount"]), 2)

        items = []
        for b in budgets:
            spent = spent_by_cat.get(b["category"].lower(), 0.0)
            limit_amt = float(b["limit_amount"])
            pct = round((spent / limit_amt) * 100.0, 1) if limit_amt > 0 else 0.0
            status = "exceeded" if spent > limit_amt else ("warning" if pct >= 80.0 else "ok")
            items.append(
                {
                    "budget_id": b["budget_id"],
                    "month": b["month"],
                    "category": b["category"],
                    "limit_amount": limit_amt,
                    "spent_amount": spent,
                    "remaining_amount": round(limit_amt - spent, 2),
                    "utilization_pct": pct,
                    "status": status,
                }
            )
        return {"month": month, "budgets": items, "count": len(items)}

    def create_goal(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        g = self.db.create_goal(
            {
                "goal_id": f"gol_{uuid.uuid4().hex[:10]}",
                "name": payload["name"].strip(),
                "target_amount": round(float(payload["target_amount"]), 2),
                "current_amount": round(float(payload.get("current_amount", 0.0)), 2),
                "target_date": payload.get("target_date", "").strip(),
                "created_at": utc_now_iso(),
            }
        )
        return self._decorate_goal(g)

    def contribute_goal(self, goal_id: str, amount: float) -> Dict[str, Any]:
        g = self.db.contribute_goal(goal_id, float(amount))
        if not g:
            raise FinanceError("GOAL_NOT_FOUND", f"Goal '{goal_id}' not found.", 404)
        return self._decorate_goal(g)

    def _decorate_goal(self, g: Dict[str, Any]) -> Dict[str, Any]:
        tgt = float(g["target_amount"])
        cur = float(g["current_amount"])
        pct = round(min(100.0, (cur / tgt) * 100.0), 1) if tgt > 0 else 0.0
        out = dict(g)
        out["progress_pct"] = pct
        out["completed"] = cur >= tgt
        return out

    def list_goals(self) -> List[Dict[str, Any]]:
        return [self._decorate_goal(g) for g in self.db.list_goals()]

    def get_summary(self, month: Optional[str] = None) -> Dict[str, Any]:
        target_month = month or today_iso()[:7]
        accounts = self.db.list_accounts()
        net_worth = round(sum(float(a["balance"]) for a in accounts), 2)
        txs = self.db.list_transactions(month=target_month)
        total_income = round(sum(float(t["amount"]) for t in txs if t["tx_type"] == "income"), 2)
        total_expense = round(sum(float(t["amount"]) for t in txs if t["tx_type"] == "expense"), 2)
        net_cashflow = round(total_income - total_expense, 2)
        savings_rate_pct = round((net_cashflow / total_income) * 100.0, 1) if total_income > 0 else 0.0

        by_cat: Dict[str, float] = {}
        for t in txs:
            if t["tx_type"] == "expense":
                by_cat[t["category"]] = round(by_cat.get(t["category"], 0.0) + float(t["amount"]), 2)

        return {
            "month": target_month,
            "net_worth": net_worth,
            "total_income": total_income,
            "total_expense": total_expense,
            "net_cashflow": net_cashflow,
            "savings_rate_pct": savings_rate_pct,
            "expense_by_category": by_cat,
            "budget_status": self.get_budget_status(target_month)["budgets"],
        }

    def export_transactions_csv(self, month: Optional[str] = None) -> str:
        txs = self.db.list_transactions(month=month)
        buf = io.StringIO()
        writer = csv.DictWriter(
            buf,
            fieldnames=["tx_id", "tx_date", "account_id", "tx_type", "category", "merchant", "amount", "note"],
        )
        writer.writeheader()
        for t in txs:
            writer.writerow({k: t[k] for k in writer.fieldnames})
        return buf.getvalue()

    def get_status(self) -> Dict[str, Any]:
        accounts = self.db.list_accounts()
        return {
            "adapter": self.adapter_name,
            "simulated": self.is_simulated,
            "accounts_count": len(accounts),
            "net_worth": round(sum(float(a["balance"]) for a in accounts), 2),
            "transactions_count": len(self.db.list_transactions()),
            "goals_count": len(self.db.list_goals()),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
