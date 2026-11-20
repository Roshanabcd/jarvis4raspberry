"""SQLite (WAL mode) persistence for simulated paper portfolio, positions, orders, and E-STOP state."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class PaperTradingStore:
    """Persists paper cash, positions, trade ledger, and E-STOP state in SQLite WAL."""

    def __init__(self, db_path: Path, starting_cash_usd: float = 10000.0) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.starting_cash_usd = starting_cash_usd
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS account_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    cash_usd REAL NOT NULL,
                    realized_pnl_usd REAL NOT NULL DEFAULT 0.0,
                    estop_active INTEGER NOT NULL DEFAULT 0,
                    estop_reason TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS paper_positions (
                    symbol TEXT PRIMARY KEY,
                    quantity REAL NOT NULL,
                    avg_entry_price REAL NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS paper_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    commission_usd REAL NOT NULL,
                    notional_usd REAL NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT NOT NULL
                );
                """
            )
            existing = conn.execute("SELECT id FROM account_state WHERE id = 1").fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO account_state (id, cash_usd, realized_pnl_usd, estop_active, estop_reason) VALUES (1, ?, 0.0, 0, '')",
                    (self.starting_cash_usd,),
                )

    def get_account(self) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM account_state WHERE id = 1").fetchone()
        return dict(row)

    def set_estop(self, active: bool, reason: str) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                "UPDATE account_state SET estop_active = ?, estop_reason = ? WHERE id = 1",
                (int(active), reason),
            )
            row = conn.execute("SELECT * FROM account_state WHERE id = 1").fetchone()
        return dict(row)

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM paper_positions WHERE symbol = ?",
                (symbol.upper(),),
            ).fetchone()
        return dict(row) if row else None

    def list_positions(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM paper_positions WHERE quantity > 0 ORDER BY symbol ASC"
            ).fetchall()
        return [dict(r) for r in rows]

    def record_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        commission_usd: float,
        notional_usd: float,
        status: str,
        reason: str,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO paper_orders
                    (created_at, symbol, side, quantity, price, commission_usd, notional_usd, status, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (now, symbol.upper(), side.upper(), quantity, price, commission_usd, notional_usd, status, reason),
            )
            row = conn.execute("SELECT * FROM paper_orders WHERE id = ?", (int(cur.lastrowid),)).fetchone()
        return dict(row)

    def apply_fill(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        commission_usd: float,
    ) -> None:
        sym = symbol.upper()
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            acct = conn.execute("SELECT * FROM account_state WHERE id = 1").fetchone()
            cash = float(acct["cash_usd"])
            realized = float(acct["realized_pnl_usd"])
            pos = conn.execute("SELECT * FROM paper_positions WHERE symbol = ?", (sym,)).fetchone()

            if side.upper() == "BUY":
                cost = quantity * price + commission_usd
                cash -= cost
                if pos:
                    old_q = float(pos["quantity"])
                    old_avg = float(pos["avg_entry_price"])
                    new_q = old_q + quantity
                    new_avg = ((old_q * old_avg) + (quantity * price)) / new_q
                    conn.execute(
                        "UPDATE paper_positions SET quantity = ?, avg_entry_price = ?, updated_at = ? WHERE symbol = ?",
                        (new_q, new_avg, now, sym),
                    )
                else:
                    conn.execute(
                        "INSERT INTO paper_positions (symbol, quantity, avg_entry_price, updated_at) VALUES (?, ?, ?, ?)",
                        (sym, quantity, price, now),
                    )
            else:
                proceeds = quantity * price - commission_usd
                cash += proceeds
                old_q = float(pos["quantity"])
                old_avg = float(pos["avg_entry_price"])
                realized += (price - old_avg) * quantity - commission_usd
                rem_q = old_q - quantity
                if rem_q <= 1e-9:
                    conn.execute("DELETE FROM paper_positions WHERE symbol = ?", (sym,))
                else:
                    conn.execute(
                        "UPDATE paper_positions SET quantity = ?, updated_at = ? WHERE symbol = ?",
                        (rem_q, now, sym),
                    )

            conn.execute(
                "UPDATE account_state SET cash_usd = ?, realized_pnl_usd = ? WHERE id = 1",
                (round(cash, 4), round(realized, 4)),
            )

    def list_orders(self, limit: int = 50) -> List[Dict[str, Any]]:
        safe_limit = max(1, min(limit, 500))
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM paper_orders ORDER BY id DESC LIMIT ?",
                (safe_limit,),
            ).fetchall()
        return [dict(r) for r in rows]
