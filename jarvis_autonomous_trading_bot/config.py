"""Environment-driven configuration for JARVIS Autonomous Trading Bot (Paper Only)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_db_path() -> Path:
    env_db = os.getenv("JARVIS_TRADING_DB_PATH")
    if env_db:
        return Path(env_db).expanduser().resolve()
    return (Path.cwd() / ".jarvis_trading_bot" / "paper_trading.db").resolve()


@dataclass(frozen=True)
class TradingBotConfig:
    """Immutable runtime settings (hard-locked to simulated paper trading)."""

    db_path: Path = field(default_factory=_default_db_path)
    paper_trading_only: bool = True  # Safety invariant: never places real brokerage orders

    starting_cash_usd: float = field(
        default_factory=lambda: float(os.getenv("JARVIS_TRADING_START_CASH", "10000.0"))
    )
    max_position_pct: float = field(
        default_factory=lambda: float(os.getenv("JARVIS_TRADING_MAX_POS_PCT", "25.0"))
    )
    max_order_usd: float = field(
        default_factory=lambda: float(os.getenv("JARVIS_TRADING_MAX_ORDER_USD", "3000.0"))
    )
    default_commission_bps: float = field(
        default_factory=lambda: float(os.getenv("JARVIS_TRADING_COMM_BPS", "5.0"))
    )
    allow_live_market_fetch: bool = field(
        default_factory=lambda: os.getenv("JARVIS_TRADING_LIVE_FETCH", "false").lower()
        in ("1", "true", "yes")
    )
