"""Report documented local CLI/API capabilities for developer automation.

This module performs bounded, read-only checks (version/help probes) and never
executes provider actions, installs packages, or exposes credentials.
"""

from __future__ import annotations

import shutil
import subprocess
from typing import Any, Dict, Iterable, List, Optional


def _run_probe(command: List[str], timeout: float = 2.0) -> Dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        output = (result.stdout or result.stderr or "").strip().splitlines()
        first_line = output[0][:200] if output else ""
        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "summary": first_line,
        }
    except FileNotFoundError:
        return {"ok": False, "returncode": 127, "summary": "not found"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "returncode": None, "summary": "probe timed out"}
    except Exception as exc:
        return {"ok": False, "returncode": None, "summary": f"{type(exc).__name__}: {exc}"}


def detect_cli_capabilities(commands: Optional[Iterable[str]] = None) -> List[Dict[str, Any]]:
    """Detect selected documented CLI tools with real, read-only status reporting."""
    default = [
        ("python3", ["python3", "--version"], "Python runtime for local scripts and tests"),
        ("pip3", ["pip3", "--version"], "Python package tooling"),
        ("git", ["git", "--version"], "Source control"),
        ("gh", ["gh", "--version"], "GitHub CLI for authorized repository automation"),
        ("ollama", ["ollama", "--version"], "Local Ollama model runtime CLI"),
        ("node", ["node", "--version"], "Node.js runtime for frontend/browser tests"),
        ("npm", ["npm", "--version"], "Node package manager"),
        ("curl", ["curl", "--version"], "HTTP client for documented endpoint checks"),
    ]
    selected = set(commands) if commands is not None else None
    capabilities: List[Dict[str, Any]] = []
    for name, probe_cmd, purpose in default:
        if selected is not None and name not in selected:
            continue
        path = shutil.which(name)
        entry: Dict[str, Any] = {
            "name": name,
            "purpose": purpose,
            "installed": bool(path),
            "path": path,
        }
        if path:
            entry["probe"] = _run_probe(probe_cmd)
            entry["status"] = "available" if entry["probe"]["ok"] else "installed_probe_failed"
        else:
            entry["probe"] = {"ok": False, "returncode": 127, "summary": "not installed"}
            entry["status"] = "missing"
        capabilities.append(entry)
    return capabilities


def summarize_provider_capabilities(brain: Any) -> List[Dict[str, Any]]:
    """Summarize provider adapter state without exposing credentials or raw bodies."""
    try:
        report = brain.get_providers_status()
        providers = report.get("providers", []) if isinstance(report, dict) else []
    except Exception as exc:
        return [{"provider": "unknown", "status": "error", "error": type(exc).__name__}]

    summary = []
    for item in providers:
        summary.append(
            {
                "provider": item.get("name") or item.get("id"),
                "model": item.get("model"),
                "status": item.get("status"),
                "credential_configured": item.get("credential_configured"),
                "verification": item.get("verification"),
                "active": item.get("active", False),
            }
        )
    return summary


def build_developer_automation_report(brain: Any = None) -> Dict[str, Any]:
    """Build a bounded developer automation status report."""
    report: Dict[str, Any] = {
        "cli_capabilities": detect_cli_capabilities(),
        "providers": summarize_provider_capabilities(brain) if brain is not None else [],
    }
    return report
