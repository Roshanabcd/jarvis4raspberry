"""Real Module Health Monitor for JARVIS Module 42.

Never infers 'healthy' from the mere existence of a ZIP archive.
Reports exact HealthStatus: healthy, degraded, unavailable, not_configured,
not_verified, or disabled.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

import httpx

from backend.app.config import ExtensionManagerConfig
from backend.models.database import ExtensionRegistryDB
from sdk.jarvis_sdk.contracts import HealthCheckResult, HealthStatus


class ModuleHealthMonitor:
    def __init__(self, db: ExtensionRegistryDB, config: Optional[ExtensionManagerConfig] = None) -> None:
        self.db = db
        self.config = config or ExtensionManagerConfig.from_env()

    async def probe_module(self, module_id: str, client: Optional[httpx.AsyncClient] = None) -> HealthCheckResult:
        mod = self.db.get_module(module_id)
        if not mod:
            return HealthCheckResult(
                module_id=module_id,
                status=HealthStatus.UNAVAILABLE,
                details={"reason": "Module not found in registry."},
            )

        if not mod["enabled"]:
            self.db.update_health(module_id, HealthStatus.DISABLED.value, None)
            return HealthCheckResult(
                module_id=module_id,
                status=HealthStatus.DISABLED,
                details={"reason": "Module is disabled."},
            )

        endpoint = mod.get("health_endpoint")
        if not endpoint or not str(endpoint).startswith(("http://", "https://")):
            self.db.update_health(module_id, HealthStatus.NOT_CONFIGURED.value, "No HTTP health_endpoint configured.")
            return HealthCheckResult(
                module_id=module_id,
                status=HealthStatus.NOT_CONFIGURED,
                endpoint=endpoint,
                details={"reason": "No live HTTP health endpoint configured; existence of archive does not imply healthy."},
            )

        started = time.monotonic()
        owns_client = client is None
        http_client = client or httpx.AsyncClient(timeout=self.config.health_timeout_seconds)
        try:
            resp = await http_client.get(endpoint)
            latency_ms = round((time.monotonic() - started) * 1000.0, 2)
            if resp.status_code == 200:
                try:
                    body = resp.json()
                except Exception:
                    body = {}
                st_str = str(body.get("status", "ok")).lower()
                if st_str in {"ok", "healthy"}:
                    status = HealthStatus.HEALTHY
                    err = None
                else:
                    status = HealthStatus.DEGRADED
                    err = f"Endpoint returned non-ok status '{st_str}'."
            elif 500 <= resp.status_code < 600:
                status = HealthStatus.UNAVAILABLE
                err = f"HTTP {resp.status_code}"
            else:
                status = HealthStatus.DEGRADED
                err = f"Unexpected HTTP {resp.status_code}"

            self.db.update_health(module_id, status.value, err)
            return HealthCheckResult(
                module_id=module_id,
                status=status,
                latency_ms=latency_ms,
                endpoint=endpoint,
                details={"http_status": resp.status_code, "error": err},
            )
        except Exception as exc:
            latency_ms = round((time.monotonic() - started) * 1000.0, 2)
            err = f"Health probe failed: {exc}"
            self.db.update_health(module_id, HealthStatus.UNAVAILABLE.value, err)
            return HealthCheckResult(
                module_id=module_id,
                status=HealthStatus.UNAVAILABLE,
                latency_ms=latency_ms,
                endpoint=endpoint,
                details={"error": err},
            )
        finally:
            if owns_client:
                await http_client.aclose()
