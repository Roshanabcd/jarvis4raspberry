"""SQLite WAL persistence layer for JARVIS Module 34 — Personal Finance Manager."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class FinanceDB:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    account_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    account_type TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    balance REAL NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS transactions (
                    tx_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    tx_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    merchant TEXT NOT NULL,
                    tx_date TEXT NOT NULL,
                    note TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
                );
                CREATE TABLE IF NOT EXISTS budgets (
                    budget_id TEXT PRIMARY KEY,
                    month TEXT NOT NULL,
                    category TEXT NOT NULL,
                    limit_amount REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(month, category)
                );
                CREATE TABLE IF NOT EXISTS savings_goals (
                    goal_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    target_amount REAL NOT NULL,
                    current_amount REAL NOT NULL,
                    target_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def create_account(self, acc: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO accounts (account_id, name, account_type, currency, balance, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (acc["account_id"], acc["name"], acc["account_type"], acc["currency"], acc["balance"], acc["created_at"]),
            )
        return acc

    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM accounts WHERE account_id = ?", (account_id,)).fetchone()
            return dict(row) if row else None

    def list_accounts(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM accounts ORDER BY created_at ASC").fetchall()
            return [dict(r) for r in rows]

    def update_account_balance(self, account_id: str, new_balance: float) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute("UPDATE accounts SET balance = ? WHERE account_id = ?", (round(new_balance, 2), account_id))
            row = conn.execute("SELECT * FROM accounts WHERE account_id = ?", (account_id,)).fetchone()
            return dict(row)

    def add_transaction(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO transactions (tx_id, account_id, tx_type, amount, category, merchant, tx_date, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tx["tx_id"],
                    tx["account_id"],
                    tx["tx_type"],
                    tx["amount"],
                    tx["category"],
                    tx["merchant"],
                    tx["tx_date"],
                    tx["note"],
                    tx["created_at"],
                ),
            )
        return tx

    def list_transactions(self, month: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        clauses = []
        params: List[Any] = []
        if month:
            clauses.append("tx_date LIKE ?")
            params.append(f"{month}-%")
        if category:
            clauses.append("LOWER(category) = LOWER(?)")
            params.append(category)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM transactions {where} ORDER BY tx_date DESC, created_at DESC",
                tuple(params),
            ).fetchall()
            return [dict(r) for r in rows]

    def upsert_budget(self, budget_id: str, month: str, category: str, limit_amount: float) -> Dict[str, Any]:
        now = utc_now_iso()
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT budget_id FROM budgets WHERE month = ? AND LOWER(category) = LOWER(?)",
                (month, category),
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE budgets SET limit_amount = ? WHERE budget_id = ?",
                    (round(limit_amount, 2), existing["budget_id"]),
                )
                row = conn.execute("SELECT * FROM budgets WHERE budget_id = ?", (existing["budget_id"],)).fetchone()
                return dict(row)
            conn.execute(
                "INSERT INTO budgets (budget_id, month, category, limit_amount, created_at) VALUES (?, ?, ?, ?, ?)",
                (budget_id, month, category, round(limit_amount, 2), now),
            )
            row = conn.execute("SELECT * FROM budgets WHERE budget_id = ?", (budget_id,)).fetchone()
            return dict(row)

    def list_budgets(self, month: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            if month:
                rows = conn.execute("SELECT * FROM budgets WHERE month = ? ORDER BY category ASC", (month,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM budgets ORDER BY month DESC, category ASC").fetchall()
            return [dict(r) for r in rows]

    def create_goal(self, goal: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO savings_goals (goal_id, name, target_amount, current_amount, target_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    goal["goal_id"],
                    goal["name"],
                    goal["target_amount"],
                    goal["current_amount"],
                    goal["target_date"],
                    goal["created_at"],
                ),
            )
        return goal

    def contribute_goal(self, goal_id: str, amount: float) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM savings_goals WHERE goal_id = ?", (goal_id,)).fetchone()
            if not row:
                return None
            new_amt = round(float(row["current_amount"]) + amount, 2)
            conn.execute("UPDATE savings_goals SET current_amount = ? WHERE goal_id = ?", (new_amt, goal_id))
            updated = conn.execute("SELECT * FROM savings_goals WHERE goal_id = ?", (goal_id,)).fetchone()
            return dict(updated)

    def list_goals(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM savings_goals ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]
