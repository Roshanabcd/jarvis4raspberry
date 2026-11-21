"""JARVIS Shared Integration SDK — Versioned Contracts (v1.0.0)."""

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

SDK_VERSION = "1.0.0"
CONTRACT_VERSION = "1.0.0"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    NOT_CONFIGURED = "not_configured"
    NOT_VERIFIED = "not_verified"
    DISABLED = "disabled"


@dataclass
class HealthCheckResult:
    module_id: str
    status: HealthStatus
    checked_at: str = field(default_factory=utc_now_iso)
    latency_ms: Optional[float] = None
    endpoint: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_id": self.module_id,
            "status": self.status.value,
            "checked_at": self.checked_at,
            "latency_ms": self.latency_ms,
            "endpoint": self.endpoint,
            "details": self.details,
        }


@dataclass
class AuthContext:
    subject: str
    roles: List[str] = field(default_factory=list)
    scopes: List[str] = field(default_factory=list)
    authenticated: bool = False
    token_id: Optional[str] = None


@dataclass
class AuthorizationDecision:
    allowed: bool
    reason: str
    required_permission: str
    evaluated_at: str = field(default_factory=utc_now_iso)


@dataclass
class ApprovalRequest:
    request_id: str = field(default_factory=lambda: f"apr_{uuid.uuid4().hex[:10]}")
    module_id: str = ""
    action: str = ""
    risk_level: str = "high"
    summary: str = ""
    status: str = "pending"
    requested_by: str = "system"
    decided_by: Optional[str] = None
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class ErrorReport:
    code: str
    message: str
    module_id: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "module_id": self.module_id,
                "details": self.details,
                "timestamp": self.timestamp,
            }
        }


@dataclass
class ModuleRegistration:
    module_id: str
    name: str
    version: str
    category: str = "extension"
    api_prefix: Optional[str] = None
    health_endpoint: Optional[str] = None
    required_permissions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    contract_version: str = CONTRACT_VERSION


class ConfigProvider(ABC):
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a module configuration value."""


class DictConfigProvider(ConfigProvider):
    def __init__(self, values: Optional[Dict[str, Any]] = None) -> None:
        self._values = dict(values or {})

    def get(self, key: str, default: Any = None) -> Any:
        return self._values.get(key, default)


class ProviderAdapter(ABC):
    """Abstract adapter contract for external AI or platform providers."""

    provider_name: str = "abstract"

    @abstractmethod
    async def invoke(self, operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a provider operation."""


class TaskOrchestratorClient(ABC):
    """Abstract contract for delegating tasks to an orchestrator (e.g., Module 18)."""

    @abstractmethod
    async def submit_task(self, title: str, capability: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a task to the host orchestrator."""


class StructuredLogger:
    """Lightweight JSON-friendly structured logger for JARVIS extensions."""

    def __init__(self, module_id: str) -> None:
        self.module_id = module_id
        self._logger = logging.getLogger(f"jarvis.{module_id}")

    def emit(self, level: str, event: str, message: str, **fields: Any) -> Dict[str, Any]:
        record = {
            "timestamp": utc_now_iso(),
            "module_id": self.module_id,
            "level": level.upper(),
            "event": event,
            "message": message,
            "fields": fields,
        }
        self._logger.log(getattr(logging, level.upper(), logging.INFO), "%s | %s", event, message)
        return record
