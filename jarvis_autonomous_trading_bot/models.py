"""Typed Pydantic v1/v2 compatible schemas for Autonomous Trading Bot."""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class Candle(BaseModel):
    timestamp: str
    open: float = Field(..., gt=0)
    high: float = Field(..., gt=0)
    low: float = Field(..., gt=0)
    close: float = Field(..., gt=0)
    volume: float = Field(default=1000.0, ge=0)


class HealthResponse(BaseModel):
    status: str = "ok"
    feature: str = "Autonomous Trading Bot"
    version: str = "1.0.0"
    mode: str = "PAPER_TRADING_ONLY"
    estop_active: bool
    cash_usd: float
    open_positions: int


class AnalyzeMarketRequest(BaseModel):
    symbol: str = Field(default="BTC-USD", min_length=1, max_length=24)
    candles: Optional[List[Candle]] = None
    sample_bars: int = Field(default=120, ge=35, le=500)


class TechnicalAnalysisResponse(BaseModel):
    symbol: str
    bars_analyzed: int
    latest_close: float
    sma_20: float
    sma_50: float
    ema_12: float
    ema_26: float
    rsi_14: float
    macd: float
    macd_signal: float
    bollinger_upper: float
    bollinger_lower: float
    atr_14: float
    signal: str  # BUY | SELL | HOLD
    confidence: float  # 0.0..1.0
    reasons: List[str]


class BacktestRequest(BaseModel):
    symbol: str = Field(default="BTC-USD", min_length=1, max_length=24)
    strategy: str = Field(default="sma_crossover", max_length=40)  # sma_crossover | rsi_mean_reversion | macd_momentum
    initial_capital: float = Field(default=10000.0, gt=100.0)
    position_size_pct: float = Field(default=50.0, gt=1.0, le=100.0)
    stop_loss_pct: float = Field(default=5.0, ge=0.0, le=50.0)
    take_profit_pct: float = Field(default=10.0, ge=0.0, le=100.0)
    commission_bps: float = Field(default=5.0, ge=0.0, le=100.0)
    candles: Optional[List[Candle]] = None
    sample_bars: int = Field(default=180, ge=60, le=600)


class BacktestTrade(BaseModel):
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl_usd: float
    return_pct: float
    exit_reason: str


class BacktestResponse(BaseModel):
    symbol: str
    strategy: str
    bars_tested: int
    initial_capital: float
    final_equity: float
    total_return_pct: float
    max_drawdown_pct: float
    win_rate_pct: float
    profit_factor: float
    sharpe_ratio: float
    total_trades: int
    trades: List[BacktestTrade]
    equity_curve: List[float]


class PaperOrderRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=24)
    side: str = Field(..., max_length=10)  # BUY | SELL
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    note: str = Field(default="manual-paper-order", max_length=200)


class OrderRecord(BaseModel):
    id: int
    created_at: str
    symbol: str
    side: str
    quantity: float
    price: float
    commission_usd: float
    notional_usd: float
    status: str  # FILLED | REJECTED
    reason: str


class PositionRecord(BaseModel):
    symbol: str
    quantity: float
    avg_entry_price: float
    market_value_usd: float


class PortfolioResponse(BaseModel):
    mode: str = "PAPER_TRADING_ONLY"
    estop_active: bool
    cash_usd: float
    positions_value_usd: float
    total_equity_usd: float
    realized_pnl_usd: float
    positions: List[PositionRecord]
    risk_limits: Dict[str, float]


class EstopRequest(BaseModel):
    active: bool
    reason: str = Field(default="Manual operator toggle", max_length=200)


class EstopResponse(BaseModel):
    estop_active: bool
    reason: str


class OrderListResponse(BaseModel):
    total: int
    orders: List[OrderRecord]
