"""FastAPI APIRouter for strictly additive integration of Autonomous Trading Bot into JARVIS OS."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from .config import TradingBotConfig
from .engine import TradingBotEngine
from .models import (
    AnalyzeMarketRequest,
    BacktestRequest,
    BacktestResponse,
    EstopRequest,
    EstopResponse,
    HealthResponse,
    OrderListResponse,
    OrderRecord,
    PaperOrderRequest,
    PortfolioResponse,
    TechnicalAnalysisResponse,
)
from .risk import RiskManager
from .storage import PaperTradingStore

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def create_router(
    config: Optional[TradingBotConfig] = None,
    prefix: str = "/api/trading-bot",
    ui_route: str = "/trading-bot",
) -> APIRouter:
    """Create a self-contained FastAPI router for JARVIS OS (Paper Trading Only)."""
    cfg = config or TradingBotConfig()
    store = PaperTradingStore(cfg.db_path, starting_cash_usd=cfg.starting_cash_usd)
    risk = RiskManager(cfg)
    engine = TradingBotEngine(cfg, store, risk)

    router = APIRouter(tags=["Autonomous Trading Bot (Paper)"])

    @router.get(ui_route, response_class=HTMLResponse, include_in_schema=False)
    async def serve_ui() -> HTMLResponse:
        if not STATIC_INDEX.exists():
            raise HTTPException(status_code=404, detail="UI bundle not found.")
        return HTMLResponse(content=STATIC_INDEX.read_text(encoding="utf-8"))

    @router.get(f"{prefix}/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        port = engine.get_portfolio()
        return HealthResponse(
            status="ok",
            estop_active=port.estop_active,
            cash_usd=port.cash_usd,
            open_positions=len(port.positions),
        )

    @router.get(f"{prefix}/portfolio", response_model=PortfolioResponse)
    async def get_portfolio() -> PortfolioResponse:
        return engine.get_portfolio()

    @router.post(f"{prefix}/estop", response_model=EstopResponse)
    async def toggle_estop(req: EstopRequest) -> EstopResponse:
        return engine.set_estop(req)

    @router.post(f"{prefix}/analyze", response_model=TechnicalAnalysisResponse)
    async def analyze_market(req: AnalyzeMarketRequest) -> TechnicalAnalysisResponse:
        return engine.analyze_market(req)

    @router.post(f"{prefix}/backtest", response_model=BacktestResponse)
    async def backtest(req: BacktestRequest) -> BacktestResponse:
        return engine.run_backtest(req)

    @router.post(f"{prefix}/orders", response_model=OrderRecord)
    async def place_order(req: PaperOrderRequest) -> OrderRecord:
        return engine.place_paper_order(req)

    @router.get(f"{prefix}/orders", response_model=OrderListResponse)
    async def list_orders(limit: int = Query(default=50, ge=1, le=500)) -> OrderListResponse:
        rows = store.list_orders(limit=limit)
        return OrderListResponse(total=len(rows), orders=[OrderRecord(**r) for r in rows])

    return router
