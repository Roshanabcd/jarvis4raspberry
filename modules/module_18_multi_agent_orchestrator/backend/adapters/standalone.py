"""Standalone compatibility harness for running Module 18 outside JARVIS Core.

Provides real in-memory/local implementations of the JARVIS adapter contracts
without fabricating external cloud or core connections.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from modules.module_18_multi_agent_orchestrator.backend.adapters.contracts import (
    CONTRACT_VERSION,
    EventCallback,
    JarvisApprovalAdapter,
    JarvisConfigAdapter,
    JarvisCoreAdapter,
    JarvisEventBusAdapter,
    JarvisLoggingAdapter,
    JarvisModelProviderAdapter,
    JarvisStorageAdapter,
)
from modules.module_18_multi_agent_orchestrator.backend.models.database import OrchestratorDatabase, utc_now_iso


class InMemoryEventBus(JarvisEventBusAdapter):
    """Async in-memory pub/sub event bus with recent event ring buffer."""

    def __init__(self, max_history: int = 250) -> None:
        self._subscribers: Dict[str, List[tuple[str, EventCallback]]] = {}
        self._history: List[Dict[str, Any]] = []
        self._max_history = max_history

    async def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        envelope = {
            "event_id": f"evt_{uuid.uuid4().hex[:10]}",
            "event_type": event_type,
            "payload": payload,
            "timestamp": utc_now_iso(),
        }
        self._history.append(envelope)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        targets = list(self._subscribers.get(event_type, [])) + list(self._subscribers.get("*", []))
        for _, cb in targets:
            try:
                await cb(event_type, envelope)
            except Exception:
                # Never let a subscriber crash the orchestrator event bus
                continue

    def subscribe(self, event_type: str, callback: EventCallback) -> str:
        sub_id = f"sub_{uuid.uuid4().hex[:8]}"
        self._subscribers.setdefault(event_type, []).append((sub_id, callback))
        return sub_id

    def unsubscribe(self, subscription_id: str) -> None:
        for key in list(self._subscribers.keys()):
            self._subscribers[key] = [
                (sid, cb) for sid, cb in self._subscribers[key] if sid != subscription_id
            ]

    def recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(reversed(self._history[-limit:]))


class LocalApprovalAdapter(JarvisApprovalAdapter):
    """SQLite-backed approval checkpoint adapter (replaceable by Module 40 later)."""

    def __init__(self, db: OrchestratorDatabase) -> None:
        self.db = db

    async def request_approval(
        self, task_id: str, workflow_id: str, prompt: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        existing = self.db.get_approval_by_task(task_id)
        if existing:
            return existing
        approval = {
            "approval_id": f"apr_{uuid.uuid4().hex[:10]}",
            "task_id": task_id,
            "workflow_id": workflow_id,
            "prompt": prompt,
            "status": "pending",
            "created_at": utc_now_iso(),
        }
        return self.db.create_approval(approval)

    async def record_decision(
        self, approval_id: str, approved: bool, decided_by: str, comment: str = ""
    ) -> Dict[str, Any]:
        status = "approved" if approved else "rejected"
        updated = self.db.decide_approval(approval_id, status, decided_by, comment)
        if not updated:
            raise KeyError(f"Approval request '{approval_id}' not found")
        return updated


class SimulatedModelProviderAdapter(JarvisModelProviderAdapter):
    """Clearly labeled deterministic local simulation provider (no external LLM calls)."""

    async def infer(self, prompt: str, task_type: str = "general", **kwargs: Any) -> Dict[str, Any]:
        return {
            "simulated": True,
            "provider": "local-deterministic-simulator",
            "task_type": task_type,
            "summary": f"[SIMULATED {task_type.upper()}] Processed prompt ({len(prompt)} chars).",
            "prompt_preview": prompt[:120],
            "timestamp": utc_now_iso(),
        }


class StructuredLoggingAdapter(JarvisLoggingAdapter):
    def __init__(self, logger_name: str = "jarvis.module18.orchestrator") -> None:
        self._logger = logging.getLogger(logger_name)

    def log(self, level: str, event_type: str, message: str, **context: Any) -> None:
        lvl = getattr(logging, level.upper(), logging.INFO)
        self._logger.log(lvl, "[%s] %s | %s", event_type, message, context)


class DictConfigAdapter(JarvisConfigAdapter):
    def __init__(self, values: Dict[str, Any]) -> None:
        self._values = dict(values)

    def get(self, key: str, default: Any = None) -> Any:
        return self._values.get(key, default)


class SQLiteStorageAdapter(JarvisStorageAdapter):
    def __init__(self, db: OrchestratorDatabase) -> None:
        self.db = db

    def health_check(self) -> Dict[str, Any]:
        return {
            "backend": "sqlite_wal",
            "db_path": self.db.db_path,
            "status": "ok",
        }


class StandaloneJarvisCoreAdapter(JarvisCoreAdapter):
    """Standalone mode core adapter — explicitly reports disconnected from live JARVIS Core."""

    def get_core_info(self) -> Dict[str, Any]:
        return {
            "mode": "standalone_compatibility_harness",
            "connected_to_jarvis_core": False,
            "contract_version": CONTRACT_VERSION,
            "note": "Running standalone. Bind a live JarvisCoreAdapter during JARVIS OS integration.",
        }

    def is_connected(self) -> bool:
        return False


@dataclass
class StandaloneHarness:
    """Bundled standalone adapters used when Module 18 runs independently."""

    core: JarvisCoreAdapter
    event_bus: InMemoryEventBus
    approvals: LocalApprovalAdapter
    model_provider: SimulatedModelProviderAdapter
    logger: StructuredLoggingAdapter
    config: DictConfigAdapter
    storage: SQLiteStorageAdapter

    @classmethod
    def create(cls, db: OrchestratorDatabase, config_values: Dict[str, Any]) -> "StandaloneHarness":
        return cls(
            core=StandaloneJarvisCoreAdapter(),
            event_bus=InMemoryEventBus(),
            approvals=LocalApprovalAdapter(db),
            model_provider=SimulatedModelProviderAdapter(),
            logger=StructuredLoggingAdapter(),
            config=DictConfigAdapter(config_values),
            storage=SQLiteStorageAdapter(db),
        )
