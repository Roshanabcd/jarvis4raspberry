"""Unified Extension Manager Engine (Module 42)."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from modules.module_42_unified_extension_manager.backend.app.config import ExtensionManagerConfig
from modules.module_42_unified_extension_manager.backend.models.database import ExtensionRegistryDB
from modules.module_42_unified_extension_manager.backend.services.archive_scanner import ModuleArchiveScanner
from modules.module_42_unified_extension_manager.backend.services.compatibility_analyzer import CompatibilityAnalyzer
from modules.module_42_unified_extension_manager.backend.services.health_monitor import ModuleHealthMonitor
from modules.module_42_unified_extension_manager.backend.services.install_planner import InstallationPlanner
from modules.module_42_unified_extension_manager.sdk.jarvis_sdk.contracts import HealthStatus, utc_now_iso
from modules.module_42_unified_extension_manager.sdk.jarvis_sdk.event_bus import EventBus, JarvisEvent


class ExtensionManagerError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class ExtensionManager:
    adapter_name: str = "local_unified_extension_manager"
    is_simulated: bool = False

    def __init__(
        self,
        config: Optional[ExtensionManagerConfig] = None,
        db: Optional[ExtensionRegistryDB] = None,
    ) -> None:
        self.config = config or ExtensionManagerConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or ExtensionRegistryDB(self.config.db_path)
        self.scanner = ModuleArchiveScanner(config=self.config)
        self.analyzer = CompatibilityAnalyzer()
        self.planner = InstallationPlanner(analyzer=self.analyzer)
        self.health_monitor = ModuleHealthMonitor(db=self.db, config=self.config)
        self.event_bus = EventBus(max_retries=2, retry_delay_seconds=0.01, persist_fn=self.db.persist_event)
        self._started_at = time.monotonic()
        self._ws_subscribers: Set[asyncio.Queue[Dict[str, Any]]] = set()

    def subscribe_ws(self) -> asyncio.Queue[Dict[str, Any]]:
        q: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=100)
        self._ws_subscribers.add(q)
        return q

    def unsubscribe_ws(self, q: asyncio.Queue[Dict[str, Any]]) -> None:
        self._ws_subscribers.discard(q)

    def _broadcast_ws(self, event_type: str, data: Dict[str, Any]) -> None:
        msg = {"event_type": event_type, "timestamp": utc_now_iso(), "data": data}
        for q in list(self._ws_subscribers):
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                pass

    def scan_folder(self, folder_path: str, register_discovered: bool = True, target_arch: str = "arm64") -> Dict[str, Any]:
        report = self.scanner.scan_folder(folder_path)
        if not report.get("exists"):
            raise ExtensionManagerError("FOLDER_NOT_FOUND", report.get("error", "Folder not found."), 404)

        enriched: List[Dict[str, Any]] = []
        for scan in report["archives"]:
            compat = self.analyzer.analyze_single(scan, target_arch=target_arch)
            entry = {**scan, "compatibility": compat}
            enriched.append(entry)

            if register_discovered:
                manifest = scan.get("manifest") if isinstance(scan.get("manifest"), dict) else {}
                stem = Path(scan["archive_name"]).stem
                module_id = str(manifest.get("module_id") or f"unverified-{stem.lower()}")
                name = str(manifest.get("name") or stem)
                version = str(manifest.get("version") or "0.0.0")
                category = str(manifest.get("category") or "unclassified")

                if not scan["valid"]:
                    status = "rejected"
                    err = "; ".join(scan["security_violations"] + scan["integrity_errors"])
                elif scan["missing_mandatory_files"]:
                    status = "incomplete"
                    err = "; ".join(f"Missing {f}" for f in scan["missing_mandatory_files"])
                else:
                    status = "discovered"
                    err = None

                self.db.upsert_module(
                    {
                        "module_id": module_id,
                        "name": name,
                        "version": version,
                        "category": category,
                        "source_archive": scan["archive_path"],
                        "integration_status": status,
                        "enabled": False,
                        "health_status": HealthStatus.NOT_VERIFIED.value,
                        "dependencies": manifest.get("dependencies") or {"python": scan["python_dependencies"]},
                        "required_permissions": manifest.get("required_permissions") or [],
                        "compatibility": compat,
                        "scan_metadata": {
                            "file_count": scan["file_count"],
                            "layout_root": scan["layout_root"],
                            "backend_entrypoints": scan["backend_entrypoints"],
                            "frontend_entrypoints": scan["frontend_entrypoints"],
                            "test_directories": scan["test_directories"],
                            "api_docs": scan["api_docs"],
                            "missing_mandatory_files": scan["missing_mandatory_files"],
                        },
                        "error_details": err,
                    }
                )

        report["archives"] = enriched
        report["cross_module_conflicts"] = self.analyzer.detect_cross_module_conflicts(self.db.list_modules())
        self.db.add_log(
            "scanner.completed",
            f"Scanned {report['archive_count']} archive(s) in {folder_path} ({report['valid_count']} valid, {report['rejected_count']} rejected)",
            details={"folder_path": folder_path, "valid": report["valid_count"], "rejected": report["rejected_count"]},
        )
        self._broadcast_ws("scanner.completed", {"archive_count": report["archive_count"], "valid": report["valid_count"]})
        return report

    def register_module(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        mod = self.db.upsert_module(payload)
        self.db.add_log("registry.registered", f"Registered module '{mod['module_id']}' v{mod['version']}", module_id=mod["module_id"])
        self._broadcast_ws("registry.updated", mod)
        return mod

    def toggle_module(self, module_id: str, enabled: bool) -> Dict[str, Any]:
        updated = self.db.set_enabled(module_id, enabled)
        if not updated:
            raise ExtensionManagerError("MODULE_NOT_FOUND", f"Module '{module_id}' not found.", 404)
        self.db.add_log(
            "registry.toggled",
            f"Module '{module_id}' {'enabled' if enabled else 'disabled'}",
            module_id=module_id,
        )
        self._broadcast_ws("registry.toggled", updated)
        return updated

    def update_module_config(
        self,
        module_id: str,
        config: Dict[str, Any],
        health_endpoint: Optional[str] = None,
        installed_location: Optional[str] = None,
    ) -> Dict[str, Any]:
        updated = self.db.update_config(module_id, config, health_endpoint, installed_location)
        if not updated:
            raise ExtensionManagerError("MODULE_NOT_FOUND", f"Module '{module_id}' not found.", 404)
        self.db.add_log("registry.config_updated", f"Updated config for '{module_id}'", module_id=module_id)
        return updated

    def build_install_plan(self, module_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        return self.planner.build_plan(self.db.list_modules(), selected_ids=module_ids or None)

    def create_approval(self, module_id: str, action: str, summary: str, requested_by: str) -> Dict[str, Any]:
        req = self.db.create_approval(module_id, action, summary, requested_by)
        self.db.add_log("approval.requested", f"Approval requested for {module_id}: {action}", module_id=module_id)
        return req

    def decide_approval(self, request_id: str, decision: str, reviewer: str, notes: str = "") -> Dict[str, Any]:
        existing = self.db.get_approval(request_id)
        if not existing:
            raise ExtensionManagerError("APPROVAL_NOT_FOUND", f"Approval request '{request_id}' not found.", 404)
        dec = decision.strip().lower()
        if dec not in {"approve", "reject"}:
            raise ExtensionManagerError("INVALID_DECISION", "Decision must be 'approve' or 'reject'.", 422)
        status = "approved" if dec == "approve" else "rejected"
        updated = self.db.decide_approval(request_id, status, reviewer, notes)
        assert updated is not None
        self.db.add_log(f"approval.{status}", f"{status.title()} by {reviewer}", module_id=existing["module_id"])
        return updated

    async def probe_health(self, module_id: str) -> Dict[str, Any]:
        res = await self.health_monitor.probe_module(module_id)
        self.db.add_log("health.probed", f"Health check for '{module_id}': {res.status.value}", module_id=module_id)
        self._broadcast_ws("health.updated", res.to_dict())
        return res.to_dict()

    async def publish_event(
        self, event_type: str, source_module: str, payload: Dict[str, Any], correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        evt = JarvisEvent(event_type=event_type, source_module=source_module, payload=payload)
        if correlation_id:
            evt.correlation_id = correlation_id
        report = await self.event_bus.publish(evt)
        self._broadcast_ws("bus.event", evt.to_dict())
        return {
            "event": evt.to_dict(),
            "delivery": {
                "delivered_count": report.delivered_count,
                "failed_count": report.failed_count,
                "failures": report.failures,
            },
        }

    def get_status(self) -> Dict[str, Any]:
        mods = self.db.list_modules()
        by_health: Dict[str, int] = {}
        for m in mods:
            by_health[m["health_status"]] = by_health.get(m["health_status"], 0) + 1
        return {
            "adapter": self.adapter_name,
            "simulated": self.is_simulated,
            "default_archives_dir": self.config.default_archives_dir,
            "total_modules": len(mods),
            "enabled_modules": sum(1 for m in mods if m["enabled"]),
            "health_breakdown": by_health,
            "pending_approvals": len(self.db.list_approvals(status="pending")),
            "cross_module_conflicts": len(self.analyzer.detect_cross_module_conflicts(mods)),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
