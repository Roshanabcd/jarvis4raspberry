"""FastAPI REST & WebSocket routes for JARVIS Module 18."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from modules.module_18_multi_agent_orchestrator.backend.models.database import utc_now_iso
from modules.module_18_multi_agent_orchestrator.backend.models.schemas import (
    AgentMessageCreateRequest,
    AgentRegisterRequest,
    AgentUpdateRequest,
    ApprovalDecisionRequest,
    ResourceLimitsRequest,
    TaskCreateRequest,
    model_to_dict,
)
from modules.module_18_multi_agent_orchestrator.backend.services.orchestrator import MultiAgentOrchestrator, OrchestratorError

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "manifest.json"


def _error_response(exc: OrchestratorError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": utc_now_iso(),
            }
        },
    )


def build_router(orchestrator: MultiAgentOrchestrator) -> APIRouter:
    router = APIRouter(prefix="/api/v1/orchestrator", tags=["JARVIS Module 18 — Multi-Agent Orchestrator"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        status = orchestrator.get_status()
        return {
            "status": "ok",
            "module_id": "jarvis-module-18-multi-agent-orchestrator",
            "version": "1.0.0",
            "contract_version": "1.0.0",
            "core_adapter": orchestrator.harness.core.get_core_info(),
            "storage": orchestrator.harness.storage.health_check(),
            "engine": status,
            "timestamp": utc_now_iso(),
        }

    @router.get("/manifest")
    async def get_manifest() -> Dict[str, Any]:
        if MANIFEST_PATH.is_file():
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        raise HTTPException(status_code=404, detail="manifest.json not found")

    @router.get("/status")
    async def get_status() -> Dict[str, Any]:
        return orchestrator.get_status()

    @router.post("/engine/pause")
    async def pause_engine() -> Dict[str, Any]:
        return await orchestrator.pause_engine()

    @router.post("/engine/resume")
    async def resume_engine() -> Dict[str, Any]:
        return await orchestrator.resume_engine()

    @router.put("/engine/limits")
    async def update_limits(body: ResourceLimitsRequest) -> Any:
        try:
            return await orchestrator.set_max_concurrency(body.max_concurrency)
        except OrchestratorError as exc:
            return _error_response(exc)

    # --- Agents ---
    @router.get("/agents")
    async def list_agents() -> Dict[str, Any]:
        agents = orchestrator.list_agents()
        return {"agents": agents, "count": len(agents)}

    @router.post("/agents", status_code=201)
    async def register_agent(body: AgentRegisterRequest) -> Any:
        try:
            return await orchestrator.register_agent(model_to_dict(body))
        except OrchestratorError as exc:
            return _error_response(exc)

    @router.patch("/agents/{agent_id}")
    async def update_agent(agent_id: str, body: AgentUpdateRequest) -> Any:
        try:
            payload = {k: (v.value if hasattr(v, "value") else v) for k, v in model_to_dict(body).items() if v is not None}
            return await orchestrator.update_agent(agent_id, payload)
        except OrchestratorError as exc:
            return _error_response(exc)

    @router.delete("/agents/{agent_id}")
    async def remove_agent(agent_id: str) -> Any:
        try:
            return await orchestrator.remove_agent(agent_id)
        except OrchestratorError as exc:
            return _error_response(exc)

    # --- Tasks ---
    @router.get("/tasks")
    async def list_tasks(
        workflow_id: Optional[str] = Query(default=None),
        status: Optional[str] = Query(default=None),
        limit: int = Query(default=200, ge=1, le=500),
    ) -> Dict[str, Any]:
        tasks = orchestrator.db.list_tasks(workflow_id=workflow_id, status=status, limit=limit)
        return {"tasks": tasks, "count": len(tasks)}

    @router.post("/tasks", status_code=201)
    async def create_task(body: TaskCreateRequest) -> Any:
        try:
            return await orchestrator.submit_task(model_to_dict(body))
        except OrchestratorError as exc:
            return _error_response(exc)

    @router.get("/tasks/{task_id}")
    async def get_task(task_id: str) -> Any:
        task = orchestrator.db.get_task(task_id)
        if not task:
            return _error_response(OrchestratorError("TASK_NOT_FOUND", f"Task '{task_id}' not found", 404))
        return task

    @router.post("/tasks/{task_id}/pause")
    async def pause_task(task_id: str) -> Any:
        try:
            return await orchestrator.pause_task(task_id)
        except OrchestratorError as exc:
            return _error_response(exc)

    @router.post("/tasks/{task_id}/resume")
    async def resume_task(task_id: str) -> Any:
        try:
            return await orchestrator.resume_task(task_id)
        except OrchestratorError as exc:
            return _error_response(exc)

    @router.post("/tasks/{task_id}/cancel")
    async def cancel_task(task_id: str, cascade: bool = Query(default=True)) -> Any:
        try:
            return await orchestrator.cancel_task(task_id, cascade=cascade)
        except OrchestratorError as exc:
            return _error_response(exc)

    # --- DAG & Workflow Aggregation ---
    @router.get("/dag")
    async def get_dag(workflow_id: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        return orchestrator.get_dag(workflow_id=workflow_id)

    @router.get("/workflows/{workflow_id}/aggregate")
    async def aggregate_workflow(workflow_id: str) -> Any:
        try:
            return await orchestrator.get_workflow_aggregation(workflow_id)
        except OrchestratorError as exc:
            return _error_response(exc)

    # --- Demo Workflow Launcher ---
    @router.post("/demo/launch", status_code=201)
    async def launch_demo_workflow() -> Dict[str, Any]:
        """Launch a 4-task parallel DAG with a human approval checkpoint (simulated demo)."""
        wf_id = f"demo-{utc_now_iso()[11:19].replace(':', '')}"
        t1 = await orchestrator.submit_task(
            {
                "title": "ResearchPi5 Architecture",
                "description": "Synthesize Raspberry Pi 5 edge orchestration constraints (simulated).",
                "workflow_id": wf_id,
                "required_capability": "research",
                "priority": 3,
                "payload": {"topic": "JARVIS OS Pi 5 Multi-Agent Scheduling", "delay_sec": 0.15},
            }
        )
        t2 = await orchestrator.submit_task(
            {
                "title": "Static Security Audit",
                "description": "Inspect orchestration worker code for risky execution patterns.",
                "workflow_id": wf_id,
                "required_capability": "code_analysis",
                "priority": 3,
                "payload": {
                    "code": "async def run_safe(x):\n    return {'ok': True, 'val': x}\n",
                    "delay_sec": 0.15,
                },
            }
        )
        t3 = await orchestrator.submit_task(
            {
                "title": "Aggregate Parallel Findings",
                "description": "Merge results from Research and Static Audit agents.",
                "workflow_id": wf_id,
                "required_capability": "aggregation",
                "priority": 4,
                "depends_on": [t1["task_id"], t2["task_id"]],
                "payload": {"numbers": [12.5, 18.0, 22.4, 15.1], "delay_sec": 0.1},
            }
        )
        t4 = await orchestrator.submit_task(
            {
                "title": "Approve Simulated Staging Release",
                "description": "Human-gated final deployment step (simulated).",
                "workflow_id": wf_id,
                "required_capability": "deploy",
                "priority": 4,
                "depends_on": [t3["task_id"]],
                "requires_approval": True,
                "approval_prompt": f"Approve simulated staging deployment for workflow '{wf_id}'?",
                "payload": {"target": "jarvis-staging-sandbox", "delay_sec": 0.1},
            }
        )
        return {
            "workflow_id": wf_id,
            "simulated": True,
            "tasks": [t1, t2, t3, t4],
        }

    # --- Approvals ---
    @router.get("/approvals")
    async def list_approvals(status: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        approvals = orchestrator.db.list_approvals(status=status)
        return {"approvals": approvals, "count": len(approvals)}

    @router.post("/approvals/{approval_id}/decide")
    async def decide_approval(approval_id: str, body: ApprovalDecisionRequest) -> Any:
        try:
            return await orchestrator.decide_approval(
                approval_id=approval_id,
                approved=body.approved,
                decided_by=body.decided_by,
                comment=body.comment,
            )
        except OrchestratorError as exc:
            return _error_response(exc)

    # --- Inter-Agent Messages ---
    @router.get("/messages")
    async def list_messages(
        workflow_id: Optional[str] = Query(default=None),
        agent_id: Optional[str] = Query(default=None),
        limit: int = Query(default=100, ge=1, le=500),
    ) -> Dict[str, Any]:
        messages = orchestrator.db.list_messages(workflow_id=workflow_id, agent_id=agent_id, limit=limit)
        return {"messages": messages, "count": len(messages)}

    @router.post("/messages", status_code=201)
    async def send_message(body: AgentMessageCreateRequest) -> Dict[str, Any]:
        return await orchestrator.send_message(model_to_dict(body))

    # --- Logs & Events ---
    @router.get("/logs")
    async def list_logs(
        task_id: Optional[str] = Query(default=None),
        agent_id: Optional[str] = Query(default=None),
        level: Optional[str] = Query(default=None),
        limit: int = Query(default=150, ge=1, le=500),
    ) -> Dict[str, Any]:
        logs = orchestrator.db.list_logs(task_id=task_id, agent_id=agent_id, level=level, limit=limit)
        return {"logs": logs, "count": len(logs)}

    @router.get("/events")
    async def recent_events(limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
        events = orchestrator.harness.event_bus.recent_events(limit=limit)
        return {"events": events, "count": len(events)}

    @router.websocket("/ws/events")
    async def ws_events(websocket: WebSocket) -> None:
        await websocket.accept()
        queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=100)

        async def _on_event(_event_type: str, envelope: Dict[str, Any]) -> None:
            if not queue.full():
                await queue.put(envelope)

        sub_id = orchestrator.harness.event_bus.subscribe("*", _on_event)
        try:
            await websocket.send_json({"event_type": "ws.connected", "status": orchestrator.get_status()})
            while True:
                recv_task = asyncio.create_task(websocket.receive_text())
                queue_task = asyncio.create_task(queue.get())
                done, pending = await asyncio.wait(
                    {recv_task, queue_task},
                    timeout=15.0,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for ptask in pending:
                    ptask.cancel()
                    try:
                        await ptask
                    except (asyncio.CancelledError, Exception):
                        pass
                if recv_task in done:
                    # Raises WebSocketDisconnect if client closed the socket
                    _ = recv_task.result()
                elif queue_task in done:
                    await websocket.send_json(queue_task.result())
                else:
                    await websocket.send_json({"event_type": "ws.heartbeat", "timestamp": utc_now_iso()})
        except (WebSocketDisconnect, RuntimeError):
            pass
        finally:
            orchestrator.harness.event_bus.unsubscribe(sub_id)

    return router
