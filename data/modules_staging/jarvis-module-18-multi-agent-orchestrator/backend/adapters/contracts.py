"""Versioned JARVIS Common Module Contract (v1.0.0) adapter interfaces.

All modules 18-41 share these documented abstract contracts so they can run
standalone today and bind cleanly to JARVIS Core services during integration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, List, Optional

CONTRACT_VERSION = "1.0.0"

EventCallback = Callable[[str, Dict[str, Any]], Awaitable[None]]


class JarvisEventBusAdapter(ABC):
    """Pub/sub event bus contract for cross-module notifications."""

    @abstractmethod
    async def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def subscribe(self, event_type: str, callback: EventCallback) -> str:
        raise NotImplementedError

    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> None:
        raise NotImplementedError


class JarvisApprovalAdapter(ABC):
    """Human-in-the-loop approval service contract (future Module 40 hook)."""

    @abstractmethod
    async def request_approval(
        self, task_id: str, workflow_id: str, prompt: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def record_decision(
        self, approval_id: str, approved: bool, decided_by: str, comment: str = ""
    ) -> Dict[str, Any]:
        raise NotImplementedError


class JarvisModelProviderAdapter(ABC):
    """Model provider contract (future Module 22 Intelligent Model Router hook)."""

    @abstractmethod
    async def infer(self, prompt: str, task_type: str = "general", **kwargs: Any) -> Dict[str, Any]:
        raise NotImplementedError


class JarvisLoggingAdapter(ABC):
    """Structured logging contract."""

    @abstractmethod
    def log(self, level: str, event_type: str, message: str, **context: Any) -> None:
        raise NotImplementedError


class JarvisConfigAdapter(ABC):
    """Configuration provider contract."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        raise NotImplementedError


class JarvisStorageAdapter(ABC):
    """Key-value / relational persistence adapter contract."""

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        raise NotImplementedError


class JarvisCoreAdapter(ABC):
    """Top-level JARVIS Core integration contract."""

    contract_version: str = CONTRACT_VERSION

    @abstractmethod
    def get_core_info(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def is_connected(self) -> bool:
        raise NotImplementedError


class JarvisOrchestratorContract(ABC):
    """Module 18 Orchestrator service interface for downstream modules (19-41)."""

    contract_version: str = CONTRACT_VERSION

    @abstractmethod
    async def register_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def submit_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def get_workflow_aggregation(self, workflow_id: str) -> Dict[str, Any]:
        raise NotImplementedError
