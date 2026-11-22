"""Pure-Python historical backtesting engine with stop-loss, take-profit, and risk metrics."""

from __future__ import annotations

import math
from typing import List

from .indicators import macd, rsi, sma
from .models import BacktestRequest, BacktestResponse, BacktestTrade, Candle


def run_backtest(req: BacktestRequest, candles: List[Candle]) -> BacktestResponse:
    closes = [c.close for c in candles]
    sma_fast = sma(closes, 10)
    sma_slow = sma(closes, 25)
    rsi_vals = rsi(closes, 14)
    macd_line, macd_sig = macd(closes, 12, 26, 9)

    cash = req.initial_capital
    qty = 0.0
    entry_price = 0.0
    entry_time = ""
    trades: List[BacktestTrade] = []
    equity_curve: List[float] = []
    comm_rate = req.commission_bps / 10000.0
    strat = req.strategy.lower()

    for i, c in enumerate(candles):
        price = c.close
        # Check open position exit conditions first
        if qty > 0.0:
            pnl_pct = ((price - entry_price) / entry_price) * 100.0
            exit_reason = ""
            if req.stop_loss_pct > 0 and pnl_pct <= -req.stop_loss_pct:
                exit_reason = "stop_loss"
            elif req.take_profit_pct > 0 and pnl_pct >= req.take_profit_pct:
                exit_reason = "take_profit"
            elif strat == "sma_crossover" and i > 25 and sma_fast[i] < sma_slow[i]:
                exit_reason = "sma_bearish_cross"
            elif strat == "rsi_mean_reversion" and rsi_vals[i] >= 65.0:
                exit_reason = "rsi_overbought_exit"
            elif strat == "macd_momentum" and i > 26 and macd_line[i] < macd_sig[i]:
                exit_reason = "macd_bearish_cross"

            if exit_reason:
                gross = qty * price
                comm = gross * comm_rate
                cash += gross - comm
                net_pnl = (price - entry_price) * qty - (entry_price * qty * comm_rate) - comm
                ret_pct = (net_pnl / max(1e-9, entry_price * qty)) * 100.0
                trades.append(
                    BacktestTrade(
                        entry_time=entry_time,
                        exit_time=c.timestamp,
                        entry_price=round(entry_price, 4),
                        exit_price=round(price, 4),
                        quantity=round(qty, 6),
                        pnl_usd=round(net_pnl, 2),
                        return_pct=round(ret_pct, 2),
                        exit_reason=exit_reason,
                    )
                )
                qty = 0.0
                entry_price = 0.0
                entry_time = ""
        else:
            # Check entry signals
            enter = False
            if strat == "sma_crossover" and i > 25 and sma_fast[i] > sma_slow[i] and sma_fast[i - 1] <= sma_slow[i - 1]:
                enter = True
            elif strat == "rsi_mean_reversion" and i > 14 and rsi_vals[i] <= 38.0:
                enter = True
            elif strat == "macd_momentum" and i > 26 and macd_line[i] > macd_sig[i] and macd_line[i - 1] <= macd_sig[i - 1]:
                enter = True

            if enter and cash > 10.0:
                alloc = cash * (req.position_size_pct / 100.0)
                comm = alloc * comm_rate
                net_alloc = max(0.0, alloc - comm)
                qty = net_alloc / price
                cash -= alloc
                entry_price = price
                entry_time = c.timestamp

        equity_curve.append(round(cash + qty * price, 2))

    # Close any open position at final bar for clean accounting
    if qty > 0.0:
        last_c = candles[-1]
        price = last_c.close
        gross = qty * price
        comm = gross * comm_rate
        cash += gross - comm
        net_pnl = (price - entry_price) * qty - (entry_price * qty * comm_rate) - comm
        ret_pct = (net_pnl / max(1e-9, entry_price * qty)) * 100.0
        trades.append(
            BacktestTrade(
                entry_time=entry_time,
                exit_time=last_c.timestamp,
                entry_price=round(entry_price, 4),
                exit_price=round(price, 4),
                quantity=round(qty, 6),
                pnl_usd=round(net_pnl, 2),
                return_pct=round(ret_pct, 2),
                exit_reason="end_of_backtest",
            )
        )
        equity_curve[-1] = round(cash, 2)

    final_eq = equity_curve[-1] if equity_curve else req.initial_capital
    total_ret = ((final_eq - req.initial_capital) / req.initial_capital) * 100.0

    # Max drawdown %
    peak = equity_curve[0] if equity_curve else req.initial_capital
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = ((peak - eq) / peak) * 100.0 if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd

    # Win rate & profit factor
    wins = [t.pnl_usd for t in trades if t.pnl_usd > 0]
    losses = [abs(t.pnl_usd) for t in trades if t.pnl_usd <= 0]
    win_rate = (len(wins) / len(trades)) * 100.0 if trades else 0.0
    gross_profit = sum(wins)
    gross_loss = sum(losses)
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0.0)

    # Annualized Sharpe Ratio (bar-to-bar returns)
    bar_returns: List[float] = []
    for i in range(1, len(equity_curve)):
        prev = equity_curve[i - 1]
        if prev > 0:
            bar_returns.append((equity_curve[i] - prev) / prev)
    if len(bar_returns) >= 2:
        mean_r = sum(bar_returns) / len(bar_returns)
        var_r = sum((r - mean_r) ** 2 for r in bar_returns) / (len(bar_returns) - 1)
        std_r = math.sqrt(var_r)
        sharpe = (mean_r / std_r) * math.sqrt(252.0) if std_r > 1e-12 else 0.0
    else:
        sharpe = 0.0

    return BacktestResponse(
        symbol=req.symbol.upper(),
        strategy=strat,
        bars_tested=len(candles),
        initial_capital=round(req.initial_capital, 2),
        final_equity=round(final_eq, 2),
        total_return_pct=round(total_ret, 2),
        max_drawdown_pct=round(max_dd, 2),
        win_rate_pct=round(win_rate, 2),
        profit_factor=round(profit_factor, 2),
        sharpe_ratio=round(sharpe, 2),
        total_trades=len(trades),
        trades=trades,
        equity_curve=equity_curve,
    )
