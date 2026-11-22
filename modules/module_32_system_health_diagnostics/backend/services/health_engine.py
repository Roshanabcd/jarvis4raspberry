"""System Health & Diagnostics Engine (Module 32).

Runs real local OS telemetry (simulated=False), historical snapshots,
threshold alerting, localhost TCP service reachability checks, and
diagnostic health scoring.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from modules.module_32_system_health_diagnostics.backend.adapters.host_probe import HostProbeAdapter, LocalLinuxHostProbe
from modules.module_32_system_health_diagnostics.backend.app.config import SystemHealthConfig
from modules.module_32_system_health_diagnostics.backend.models.database import SystemHealthDB, utc_now_iso

ALLOWED_PROBE_HOSTS = {"127.0.0.1", "localhost", "::1"}


class SystemHealthError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def _compare(lhs: float, op: str, rhs: float) -> bool:
    if op == ">":
        return lhs > rhs
    if op == ">=":
        return lhs >= rhs
    if op == "<":
        return lhs < rhs
    return lhs <= rhs


class SystemHealthEngine:
    def __init__(
        self,
        config: Optional[SystemHealthConfig] = None,
        db: Optional[SystemHealthDB] = None,
        probe: Optional[HostProbeAdapter] = None,
    ) -> None:
        self.config = config or SystemHealthConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or SystemHealthDB(self.config.db_path)
        self.probe = probe or LocalLinuxHostProbe()
        self._started_at = time.monotonic()

    def get_live_metrics(self) -> Dict[str, Any]:
        return self.probe.collect_metrics(disk_path=self.config.monitor_disk_path)

    def capture_snapshot(self) -> Dict[str, Any]:
        metrics = self.get_live_metrics()
        snap = self.db.add_snapshot(f"snp_{uuid.uuid4().hex[:10]}", metrics)
        triggered_alerts = self._evaluate_rules(metrics)
        return {"snapshot": snap, "triggered_alerts": triggered_alerts}

    def _evaluate_rules(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        fired: List[Dict[str, Any]] = []
        for rule in self.db.list_rules():
            val = metrics.get(rule["metric_key"])
            if val is None:
                continue
            num = float(val)
            if _compare(num, rule["operator"], float(rule["threshold"])):
                alert = self.db.add_alert(
                    {
                        "alert_id": f"alt_{uuid.uuid4().hex[:10]}",
                        "rule_id": rule["rule_id"],
                        "rule_name": rule["name"],
                        "metric_key": rule["metric_key"],
                        "metric_value": num,
                        "threshold": float(rule["threshold"]),
                        "severity": rule["severity"],
                        "acknowledged": False,
                        "created_at": utc_now_iso(),
                    }
                )
                fired.append(alert)
        return fired

    def create_rule(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.db.create_rule(
            {
                "rule_id": f"rul_{uuid.uuid4().hex[:10]}",
                "name": payload["name"].strip(),
                "metric_key": payload["metric_key"],
                "operator": payload["operator"],
                "threshold": float(payload["threshold"]),
                "severity": payload.get("severity", "warning"),
                "created_at": utc_now_iso(),
            }
        )

    def ack_alert(self, alert_id: str) -> Dict[str, Any]:
        alert = self.db.ack_alert(alert_id)
        if not alert:
            raise SystemHealthError("ALERT_NOT_FOUND", f"Alert '{alert_id}' not found.", 404)
        return alert

    def register_service(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        host = payload.get("host", "127.0.0.1").strip().lower()
        if host not in ALLOWED_PROBE_HOSTS:
            raise SystemHealthError(
                "HOST_NOT_ALLOWED",
                f"Service probes are restricted to localhost ({', '.join(sorted(ALLOWED_PROBE_HOSTS))}).",
                403,
            )
        return self.db.create_service(
            {
                "service_id": f"svc_{uuid.uuid4().hex[:10]}",
                "name": payload["name"].strip(),
                "host": host,
                "port": int(payload["port"]),
                "last_status": "unknown",
                "last_latency_ms": None,
                "last_checked_at": None,
            }
        )

    def probe_all_services(self) -> Dict[str, Any]:
        results = []
        for svc in self.db.list_services():
            st, lat = self.probe.probe_tcp(svc["host"], int(svc["port"]), timeout_s=self.config.probe_timeout_s)
            updated = self.db.update_service_probe(svc["service_id"], st, lat)
            results.append(updated)
        return {"services": results, "count": len(results)}

    def run_diagnostics(self) -> Dict[str, Any]:
        cap = self.capture_snapshot()
        metrics = cap["snapshot"]["metrics"]
        svc_res = self.probe_all_services()
        open_alerts = self.db.list_alerts(unacknowledged_only=True)

        score = 100
        recs: List[str] = []
        if metrics["memory_used_pct"] >= 85.0:
            score -= 20
            recs.append("Memory usage above 85% — inspect high-RAM processes or enable swap tuning.")
        if metrics["disk_used_pct"] >= 85.0:
            score -= 20
            recs.append("Disk usage above 85% — archive old logs or prune unused artifacts.")
        if metrics.get("cpu_temp_c") is not None and float(metrics["cpu_temp_c"]) >= 75.0:
            score -= 15
            recs.append("CPU temperature above 75°C — verify active cooling on Raspberry Pi 5.")

        down_services = [s["name"] for s in svc_res["services"] if s["last_status"] != "up"]
        if down_services:
            score -= min(30, 10 * len(down_services))
            recs.append(f"Unreachable local services: {', '.join(down_services)}.")

        if open_alerts:
            score -= min(15, 5 * len(open_alerts))

        score = max(0, score)
        if not recs:
            recs.append("All checked host metrics and registered local services are within nominal thresholds.")

        summary = {
            "metrics": metrics,
            "services": svc_res["services"],
            "open_alerts_count": len(open_alerts),
            "recommendations": recs,
        }
        return self.db.add_diagnostic_run(f"dgn_{uuid.uuid4().hex[:10]}", score, summary)

    def get_status(self) -> Dict[str, Any]:
        metrics = self.get_live_metrics()
        return {
            "adapter": self.probe.adapter_name,
            "simulated": self.probe.is_simulated,
            "hostname": metrics["hostname"],
            "load_1m": metrics["load_1m"],
            "memory_used_pct": metrics["memory_used_pct"],
            "disk_used_pct": metrics["disk_used_pct"],
            "cpu_temp_c": metrics["cpu_temp_c"],
            "open_alerts_count": len(self.db.list_alerts(unacknowledged_only=True)),
            "services_count": len(self.db.list_services()),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
