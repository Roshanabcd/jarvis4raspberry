"""Sample JARVIS Extension built on top of JARVIS SDK v1.0.0."""

from __future__ import annotations

from typing import Any, Dict, List

from sdk.jarvis_sdk import (
    HealthCheckResult,
    HealthStatus,
    JarvisEvent,
    ModuleRegistration,
    ReferenceHostAdapter,
    StructuredLogger,
)


class SampleDiagnosticsExtension:
    """Minimal, real extension demonstrating SDK registration, event handling, and health reporting."""

    MODULE_ID = "jarvis-sample-diagnostics-extension"

    def __init__(self, host: ReferenceHostAdapter) -> None:
        self.host = host
        self.logger = StructuredLogger(self.MODULE_ID)
        self.received_events: List[Dict[str, Any]] = []
        self.registration = ModuleRegistration(
            module_id=self.MODULE_ID,
            name="Sample Diagnostics Extension",
            version="1.0.0",
            category="diagnostics",
            api_prefix="/api/v1/sample-diagnostics",
            health_endpoint="/api/v1/sample-diagnostics/health",
            required_permissions=["diagnostics.read"],
            dependencies=[],
        )
        self.host.register_module(self.registration, health_fn=self.health_check)
        self.sub_id = self.host.event_bus.subscribe("extension.ping", self.on_ping)

    async def on_ping(self, event: JarvisEvent) -> None:
        self.received_events.append(event.to_dict())
        self.logger.emit("INFO", "sample.ping_received", "Handled extension.ping event", event_id=event.event_id)

    def health_check(self) -> HealthCheckResult:
        return HealthCheckResult(
            module_id=self.MODULE_ID,
            status=HealthStatus.HEALTHY,
            details={"received_events": len(self.received_events)},
        )
