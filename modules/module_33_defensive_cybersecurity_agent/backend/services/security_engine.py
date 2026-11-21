"""Defensive Cybersecurity Agent Engine (Module 33)."""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from modules.module_33_defensive_cybersecurity_agent.backend.adapters.defensive_scanner import LocalDefensiveScanner
from modules.module_33_defensive_cybersecurity_agent.backend.app.config import CyberSecurityConfig
from modules.module_33_defensive_cybersecurity_agent.backend.models.database import CyberSecurityDB, utc_now_iso


class CyberSecurityError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class DefensiveSecurityEngine:
    def __init__(
        self,
        config: Optional[CyberSecurityConfig] = None,
        db: Optional[CyberSecurityDB] = None,
        scanner: Optional[LocalDefensiveScanner] = None,
    ) -> None:
        self.config = config or CyberSecurityConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or CyberSecurityDB(self.config.db_path)
        self.scanner = scanner or LocalDefensiveScanner()
        self._started_at = time.monotonic()

    def _resolve_sandbox_path(self, relative_path: str) -> Path:
        root = Path(self.config.scan_root).resolve()
        candidate = (root / relative_path).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise CyberSecurityError(
                "PATH_OUTSIDE_SANDBOX",
                f"Path '{relative_path}' escapes the configured defensive scan root.",
                403,
            ) from exc
        if not candidate.exists():
            raise CyberSecurityError("PATH_NOT_FOUND", f"Path '{relative_path}' does not exist.", 404)
        return candidate

    def _record_incident(self, category: str, severity: str, title: str, detail: str, remediation: str) -> Dict[str, Any]:
        now = utc_now_iso()
        return self.db.add_incident(
            {
                "incident_id": f"inc_{uuid.uuid4().hex[:10]}",
                "category": category,
                "severity": severity,
                "title": title,
                "detail": detail,
                "remediation": remediation,
                "status": "open",
                "resolution_note": "",
                "created_at": now,
                "updated_at": now,
            }
        )

    def run_secret_scan(self, relative_path: str = ".") -> Dict[str, Any]:
        root = Path(self.config.scan_root).resolve()
        target = self._resolve_sandbox_path(relative_path)
        files_scanned, findings = self.scanner.scan_directory(target, root)
        run = self.db.add_scan_run(f"scn_{uuid.uuid4().hex[:10]}", relative_path, files_scanned, findings)
        for f in findings:
            self._record_incident(
                category=f"secret_scan.{f['rule']}",
                severity=f["severity"],
                title=f"Detected {f['rule']} in {f['file']}",
                detail=f"Line {f['line']}: masked={f['masked_match']}",
                remediation=f["remediation"],
            )
        return run

    def create_fim_baseline(self, name: str, relative_path: str = ".") -> Dict[str, Any]:
        root = Path(self.config.scan_root).resolve()
        target = self._resolve_sandbox_path(relative_path)
        hashes = self.scanner.compute_sha256_map(target, root)
        return self.db.create_baseline(f"fim_{uuid.uuid4().hex[:10]}", name.strip(), relative_path, hashes)

    def verify_fim_baseline(self, baseline_id: str) -> Dict[str, Any]:
        baseline = self.db.get_baseline(baseline_id)
        if not baseline:
            raise CyberSecurityError("BASELINE_NOT_FOUND", f"Baseline '{baseline_id}' not found.", 404)
        root = Path(self.config.scan_root).resolve()
        target = self._resolve_sandbox_path(baseline["target_path"])
        current = self.scanner.compute_sha256_map(target, root)
        expected = baseline["hashes"]

        modified = sorted(k for k in expected if k in current and current[k] != expected[k])
        added = sorted(k for k in current if k not in expected)
        deleted = sorted(k for k in expected if k not in current)
        drift_detected = bool(modified or added or deleted)

        if drift_detected:
            self._record_incident(
                category="fim.drift",
                severity="high",
                title=f"File integrity drift on baseline '{baseline['name']}'",
                detail=f"modified={modified}, added={added}, deleted={deleted}",
                remediation="Inspect unexpected file changes and re-establish baseline only after verifying legitimacy.",
            )

        return {
            "baseline_id": baseline_id,
            "baseline_name": baseline["name"],
            "drift_detected": drift_detected,
            "modified": modified,
            "added": added,
            "deleted": deleted,
        }

    def analyze_logs(self, source: str, lines: List[str]) -> Dict[str, Any]:
        anomalies = self.scanner.analyze_log_lines(
            source=source,
            lines=lines,
            brute_force_threshold=self.config.brute_force_threshold,
        )
        created = [
            self._record_incident(
                category=a["category"],
                severity=a["severity"],
                title=a["title"],
                detail=a["detail"],
                remediation=a["remediation"],
            )
            for a in anomalies
        ]
        return {"source": source, "lines_analyzed": len(lines), "incidents_created": len(created), "incidents": created}

    def resolve_incident(self, incident_id: str, resolution_note: str) -> Dict[str, Any]:
        inc = self.db.resolve_incident(incident_id, resolution_note.strip())
        if not inc:
            raise CyberSecurityError("INCIDENT_NOT_FOUND", f"Incident '{incident_id}' not found.", 404)
        return inc

    def get_status(self) -> Dict[str, Any]:
        open_inc = self.db.list_incidents(status="open")
        penalties = {"critical": 25, "high": 15, "medium": 8, "low": 3}
        deduction = sum(penalties.get(i["severity"], 5) for i in open_inc)
        score = max(0, 100 - deduction)
        return {
            "adapter": self.scanner.adapter_name,
            "simulated": self.scanner.is_simulated,
            "posture_score": score,
            "open_incidents": len(open_inc),
            "baselines_count": len(self.db.list_baselines()),
            "scans_count": len(self.db.list_scans()),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
