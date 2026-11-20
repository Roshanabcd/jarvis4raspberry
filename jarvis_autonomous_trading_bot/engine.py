"""Core Autonomous Trading Bot engine (paper trading, technical analysis, backtesting, risk)."""

from __future__ import annotations

from typing import List

from .backtester import run_backtest
from .config import TradingBotConfig
from .indicators import atr, bollinger_bands, ema, macd, rsi, sma
from .market_data import generate_synthetic_candles
from .models import (
    AnalyzeMarketRequest,
    BacktestRequest,
    BacktestResponse,
    Candle,
    EstopRequest,
    EstopResponse,
    OrderRecord,
    PaperOrderRequest,
    PortfolioResponse,
    PositionRecord,
    TechnicalAnalysisResponse,
)
from .risk import RiskManager
from .storage import PaperTradingStore


class TradingBotEngine:
    """Coordinates simulated paper execution, technical analysis, and backtesting."""

    def __init__(
        self,
        config: TradingBotConfig,
        store: PaperTradingStore,
        risk: RiskManager,
    ) -> None:
        self.config = config
        self.store = store
        self.risk = risk

    @staticmethod
    def _get_candles(symbol: str, provided: List[Candle] | None, bars: int) -> List[Candle]:
        if provided and len(provided) >= 20:
            return provided
        return generate_synthetic_candles(symbol=symbol, bars=bars)

    def analyze_market(self, req: AnalyzeMarketRequest) -> TechnicalAnalysisResponse:
        candles = self._get_candles(req.symbol, req.candles, req.sample_bars)
        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]

        sma20 = sma(closes, 20)[-1]
        sma50 = sma(closes, 50)[-1]
        ema12 = ema(closes, 12)[-1]
        ema26 = ema(closes, 26)[-1]
        rsi14 = rsi(closes, 14)[-1]
        macd_l, macd_s = macd(closes, 12, 26, 9)
        bb_u, _, bb_l = bollinger_bands(closes, 20, 2.0)
        atr14 = atr(highs, lows, closes, 14)[-1]
        latest = closes[-1]

        score = 0
        reasons: List[str] = []

        if sma20 > sma50:
            score += 1
            reasons.append("Bullish trend: SMA(20) is above SMA(50).")
        else:
            score -= 1
            reasons.append("Bearish trend: SMA(20) is below SMA(50).")

        if macd_l[-1] > macd_s[-1]:
            score += 1
            reasons.append("Positive momentum: MACD line is above signal line.")
        else:
            score -= 1
            reasons.append("Negative momentum: MACD line is below signal line.")

        if rsi14 < 35:
            score += 1
            reasons.append(f"Oversold RSI(14)={rsi14:.1f} suggests potential mean-reversion bounce.")
        elif rsi14 > 65:
            score -= 1
            reasons.append(f"Overbought RSI(14)={rsi14:.1f} suggests pullback risk.")
        else:
            reasons.append(f"Neutral RSI(14)={rsi14:.1f} inside balanced momentum zone.")

        if score >= 2:
            signal = "BUY"
        elif score <= -2:
            signal = "SELL"
        else:
            signal = "HOLD"

        confidence = round(min(0.95, 0.45 + abs(score) * 0.16), 2)

        return TechnicalAnalysisResponse(
            symbol=req.symbol.upper(),
            bars_analyzed=len(candles),
            latest_close=round(latest, 4),
            sma_20=round(sma20, 4),
            sma_50=round(sma50, 4),
            ema_12=round(ema12, 4),
            ema_26=round(ema26, 4),
            rsi_14=round(rsi14, 2),
            macd=round(macd_l[-1], 4),
            macd_signal=round(macd_s[-1], 4),
            bollinger_upper=round(bb_u[-1], 4),
            bollinger_lower=round(bb_l[-1], 4),
            atr_14=round(atr14, 4),
            signal=signal,
            confidence=confidence,
            reasons=reasons,
        )

    def run_backtest(self, req: BacktestRequest) -> BacktestResponse:
        candles = self._get_candles(req.symbol, req.candles, req.sample_bars)
        return run_backtest(req, candles)

    def get_portfolio(self) -> PortfolioResponse:
        acct = self.store.get_account()
        raw_pos = self.store.list_positions()
        positions: List[PositionRecord] = []
        pos_val = 0.0
        for p in raw_pos:
            val = float(p["quantity"]) * float(p["avg_entry_price"])
            pos_val += val
            positions.append(
                PositionRecord(
                    symbol=str(p["symbol"]),
                    quantity=round(float(p["quantity"]), 6),
                    avg_entry_price=round(float(p["avg_entry_price"]), 4),
                    market_value_usd=round(val, 2),
                )
            )
        cash = float(acct["cash_usd"])
        return PortfolioResponse(
            estop_active=bool(acct["estop_active"]),
            cash_usd=round(cash, 2),
            positions_value_usd=round(pos_val, 2),
            total_equity_usd=round(cash + pos_val, 2),
            realized_pnl_usd=round(float(acct["realized_pnl_usd"]), 2),
            positions=positions,
            risk_limits={
                "max_position_pct": self.config.max_position_pct,
                "max_order_usd": self.config.max_order_usd,
                "commission_bps": self.config.default_commission_bps,
            },
        )

    def place_paper_order(self, req: PaperOrderRequest) -> OrderRecord:
        portfolio = self.get_portfolio()
        existing = self.store.get_position(req.symbol)
        notional = round(req.quantity * req.price, 4)
        commission = round(notional * (self.config.default_commission_bps / 10000.0), 4)

        approved, reason = self.risk.validate_order(
            side=req.side,
            quantity=req.quantity,
            price=req.price,
            cash_usd=portfolio.cash_usd,
            total_equity_usd=portfolio.total_equity_usd,
            existing_position=existing,
            estop_active=portfolio.estop_active,
        )

        if not approved:
            rec = self.store.record_order(
                symbol=req.symbol,
                side=req.side,
                quantity=req.quantity,
                price=req.price,
                commission_usd=0.0,
                notional_usd=notional,
                status="REJECTED",
                reason=reason,
            )
            return OrderRecord(**rec)

        self.store.apply_fill(
            symbol=req.symbol,
            side=req.side,
            quantity=req.quantity,
            price=req.price,
            commission_usd=commission,
        )
        rec = self.store.record_order(
            symbol=req.symbol,
            side=req.side,
            quantity=req.quantity,
            price=req.price,
            commission_usd=commission,
            notional_usd=notional,
            status="FILLED",
            reason=f"{reason} ({req.note})",
        )
        return OrderRecord(**rec)

    def set_estop(self, req: EstopRequest) -> EstopResponse:
        acct = self.store.set_estop(req.active, req.reason)
        return EstopResponse(estop_active=bool(acct["estop_active"]), reason=str(acct["estop_reason"]))
