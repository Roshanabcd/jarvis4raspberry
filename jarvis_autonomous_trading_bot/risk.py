"""Risk-management guardrails for simulated paper trading execution."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from .config import TradingBotConfig


class RiskManager:
    """Validates every simulated order against E-STOP, cash, position size, and notional caps."""

    def __init__(self, config: TradingBotConfig) -> None:
        self.config = config

    def validate_order(
        self,
        side: str,
        quantity: float,
        price: float,
        cash_usd: float,
        total_equity_usd: float,
        existing_position: Optional[Dict[str, object]],
        estop_active: bool,
    ) -> Tuple[bool, str]:
        if not self.config.paper_trading_only:
            return False, "Safety lock error: live trading is disabled in this module."

        if estop_active:
            return False, "REJECTED: E-STOP kill switch is active. Disarm E-STOP before placing orders."

        side_u = side.upper()
        if side_u not in ("BUY", "SELL"):
            return False, "REJECTED: Order side must be BUY or SELL."

        notional = quantity * price
        commission = notional * (self.config.default_commission_bps / 10000.0)

        if notional > self.config.max_order_usd:
            return (
                False,
                f"REJECTED: Order notional (${notional:.2f}) exceeds max single order limit (${self.config.max_order_usd:.2f}).",
            )

        if side_u == "BUY":
            if notional + commission > cash_usd:
                return (
                    False,
                    f"REJECTED: Insufficient paper cash (${cash_usd:.2f} available, ${notional + commission:.2f} required).",
                )
            existing_val = float(existing_position["quantity"]) * price if existing_position else 0.0
            new_pos_pct = ((existing_val + notional) / max(1.0, total_equity_usd)) * 100.0
            if new_pos_pct > self.config.max_position_pct:
                return (
                    False,
                    f"REJECTED: Resulting position ({new_pos_pct:.1f}% of equity) exceeds max position limit ({self.config.max_position_pct:.1f}%).",
                )
            return True, "Approved by paper risk manager."

        # SELL checks (no naked shorting in paper safety mode)
        held_qty = float(existing_position["quantity"]) if existing_position else 0.0
        if quantity > held_qty + 1e-9:
            return (
                False,
                f"REJECTED: Cannot sell {quantity} units (only {held_qty:.4f} held; short-selling disabled).",
            )
        return True, "Approved by paper risk manager."
