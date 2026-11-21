"""Reference Host Adapter for JARVIS SDK (adaptable to any host architecture)."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from modules.module_42_unified_extension_manager.sdk.jarvis_sdk.contracts import (
    ApprovalRequest,
    AuthContext,
    AuthorizationDecision,
    ConfigProvider,
    DictConfigProvider,
    HealthCheckResult,
    HealthStatus,
    ModuleRegistration,
    StructuredLogger,
)
from modules.module_42_unified_extension_manager.sdk.jarvis_sdk.event_bus import EventBus, JarvisEvent


class ReferenceHostAdapter:
    """
    Architecture-agnostic reference host implementing the JARVIS SDK contract.
    Host integrators can wrap their existing FastAPI/Flask/custom core around this
    interface without assuming uninspected core routes.
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        config_provider: Optional[ConfigProvider] = None,
    ) -> None:
        self.event_bus = event_bus or EventBus()
        self.config = config_provider or DictConfigProvider()
        self._modules: Dict[str, ModuleRegistration] = {}
        self._health_callbacks: Dict[str, Callable[[], HealthCheckResult]] = {}
        self._approvals: Dict[str, ApprovalRequest] = {}
        self.logger = StructuredLogger("jarvis-reference-host")

    def register_module(
        self,
        registration: ModuleRegistration,
        health_fn: Optional[Callable[[], HealthCheckResult]] = None,
    ) -> ModuleRegistration:
        self._modules[registration.module_id] = registration
        if health_fn:
            self._health_callbacks[registration.module_id] = health_fn
        self.logger.emit("INFO", "sdk.module_registered", f"Registered {registration.module_id} v{registration.version}")
        return registration

    def discover_modules(self, category: Optional[str] = None) -> List[ModuleRegistration]:
        mods = list(self._modules.values())
        if category:
            mods = [m for m in mods if m.category == category]
        return mods

    def check_authorization(self, auth: AuthContext, required_permission: str) -> AuthorizationDecision:
        if not auth.authenticated:
            return AuthorizationDecision(False, "Subject is not authenticated.", required_permission)
        if "admin" in auth.roles or required_permission in auth.scopes or "*" in auth.scopes:
            return AuthorizationDecision(True, "Permission granted.", required_permission)
        return AuthorizationDecision(False, f"Missing required scope '{required_permission}'.", required_permission)

    def request_approval(self, req: ApprovalRequest) -> ApprovalRequest:
        self._approvals[req.request_id] = req
        return req

    def check_module_health(self, module_id: str) -> HealthCheckResult:
        if module_id not in self._modules:
            return HealthCheckResult(module_id=module_id, status=HealthStatus.UNAVAILABLE, details={"reason": "Not registered"})
        fn = self._health_callbacks.get(module_id)
        if not fn:
            return HealthCheckResult(module_id=module_id, status=HealthStatus.NOT_VERIFIED, details={"reason": "No health callback registered"})
        return fn()

    async def publish_event(self, event: JarvisEvent) -> Dict[str, Any]:
        report = await self.event_bus.publish(event)
        return {
            "event_id": report.event_id,
            "delivered_count": report.delivered_count,
            "failed_count": report.failed_count,
        }
