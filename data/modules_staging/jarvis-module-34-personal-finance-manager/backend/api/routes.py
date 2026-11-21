"""FastAPI REST & WebSocket routes for JARVIS Module 34 — Personal Finance Manager."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, PlainTextResponse

from backend.models.database import today_iso, utc_now_iso
from backend.models.schemas import (
    AccountCreateRequest,
    BudgetUpsertRequest,
    GoalContributeRequest,
    GoalCreateRequest,
    TransactionCreateRequest,
    model_to_dict,
)
from backend.services.finance_engine import FinanceEngine, FinanceError

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _err(exc: FinanceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "timestamp": utc_now_iso()}},
    )


def build_router(engine: FinanceEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/finance", tags=["JARVIS Module 34 — Personal Finance Manager"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "module_id": "jarvis-module-34-personal-finance-manager",
            "version": "1.0.0",
            "contract_version": "1.0.0",
            "simulated": engine.is_simulated,
            "timestamp": utc_now_iso(),
        }

    @router.get("/manifest")
    async def manifest() -> Dict[str, Any]:
        if MANIFEST_PATH.is_file():
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        raise HTTPException(status_code=404, detail="manifest.json not found")

    @router.get("/status")
    async def status() -> Dict[str, Any]:
        return engine.get_status()

    @router.get("/accounts")
    async def list_accounts() -> Dict[str, Any]:
        accs = engine.db.list_accounts()
        return {"accounts": accs, "count": len(accs)}

    @router.post("/accounts", status_code=201)
    async def create_account(body: AccountCreateRequest) -> Dict[str, Any]:
        return engine.create_account(model_to_dict(body))

    @router.get("/transactions")
    async def list_transactions(
        month: Optional[str] = Query(default=None),
        category: Optional[str] = Query(default=None),
    ) -> Dict[str, Any]:
        txs = engine.db.list_transactions(month=month, category=category)
        return {"transactions": txs, "count": len(txs)}

    @router.post("/transactions", status_code=201)
    async def record_transaction(body: TransactionCreateRequest) -> Any:
        try:
            return engine.record_transaction(model_to_dict(body))
        except FinanceError as exc:
            return _err(exc)

    @router.get("/transactions/export.csv")
    async def export_csv(month: Optional[str] = Query(default=None)) -> PlainTextResponse:
        csv_text = engine.export_transactions_csv(month=month)
        return PlainTextResponse(content=csv_text, media_type="text/csv")

    @router.post("/budgets", status_code=201)
    async def upsert_budget(body: BudgetUpsertRequest) -> Dict[str, Any]:
        return engine.upsert_budget(model_to_dict(body))

    @router.get("/budgets/status")
    async def budget_status(month: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        return engine.get_budget_status(month or today_iso()[:7])

    @router.get("/goals")
    async def list_goals() -> Dict[str, Any]:
        goals = engine.list_goals()
        return {"goals": goals, "count": len(goals)}

    @router.post("/goals", status_code=201)
    async def create_goal(body: GoalCreateRequest) -> Dict[str, Any]:
        return engine.create_goal(model_to_dict(body))

    @router.post("/goals/{goal_id}/contribute")
    async def contribute_goal(goal_id: str, body: GoalContributeRequest) -> Any:
        try:
            return engine.contribute_goal(goal_id, body.amount)
        except FinanceError as exc:
            return _err(exc)

    @router.get("/summary")
    async def summary(month: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        return engine.get_summary(month=month)

    @router.websocket("/ws/updates")
    async def ws_updates(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            await websocket.send_json({"event_type": "ws.connected", "status": engine.get_status()})
            while True:
                recv = asyncio.create_task(websocket.receive_text())
                done, _ = await asyncio.wait({recv}, timeout=10.0)
                if recv in done:
                    _ = recv.result()
                else:
                    recv.cancel()
                    try:
                        await recv
                    except (asyncio.CancelledError, Exception):
                        pass
                    await websocket.send_json({"event_type": "ws.heartbeat", "status": engine.get_status()})
        except (WebSocketDisconnect, RuntimeError):
            pass

    return router
