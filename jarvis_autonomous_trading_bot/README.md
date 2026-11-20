# JARVIS OS — Feature #6: Autonomous Trading Bot (Paper Trading Only)

Strictly additive, Raspberry Pi 5-friendly Experimental module for **JARVIS OS**:
- **Safety-Locked Paper Trading Brokerage** (`PAPER_TRADING_ONLY`, never places real-money orders) with SQLite (WAL mode) cash, positions, and order audit ledger
- **E-STOP Kill Switch & Risk Manager** (max position size %, max single order value, cash & no-short guards)
- **Pure-Python Technical Analysis** (SMA, EMA, RSI-14, MACD, Bollinger Bands, ATR-14, composite BUY/SELL/HOLD signal)
- **Historical Backtesting Engine** (`sma_crossover`, `rsi_mean_reversion`, `macd_momentum`) with stop-loss, take-profit, commission bps, max drawdown, win rate, profit factor, and Sharpe ratio
- **JARVIS OS Dark Cyber Web UI** at `/trading-bot`

## Quick Start (Standalone on Raspberry Pi 5)

```bash
cd ~/.gemini/antigravity/scratch/jarvis-os
unzip /path/to/jarvis_autonomous_trading_bot.zip -d features/
cd features

uvicorn jarvis_autonomous_trading_bot.app:app --host 127.0.0.1 --port 8016
```

Open `http://127.0.0.1:8016/trading-bot`.

## Run Tests

```bash
python3 -m unittest discover -s jarvis_autonomous_trading_bot/tests -v
# or with pytest:
pytest jarvis_autonomous_trading_bot/tests -v
```
