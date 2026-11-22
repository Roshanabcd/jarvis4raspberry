"""Integration Compatibility Analyzer for JARVIS Module 42.

Distinguishes verified compatibility, metadata-inferred compatibility, unverified
requirements, cross-module conflicts, missing information, and unsupported ARM64/Linux
dependencies without executing untrusted archive code.
"""

from __future__ import annotations

import platform
import re
from typing import Any, Dict, List, Tuple

ARM64_UNSUPPORTED_OR_RISKY = {
    "pywin32": "Windows-only package (unsupported on Linux ARM64 / Raspberry Pi 5).",
    "win32gui": "Windows-only GUI package (unsupported on Linux ARM64).",
    "comtypes": "Windows COM automation library (unsupported on Linux).",
    "nvidia-cuda-runtime-cu12": "Requires NVIDIA CUDA GPU (unsupported on Raspberry Pi 5 ARM64).",
    "torch-tensorrt": "Requires NVIDIA TensorRT GPU runtime (unsupported on Pi 5).",
    "bitsandbytes": "Requires CUDA GPU acceleration for 8-bit/4-bit quantization.",
}

HEAVYWEIGHT_PACKAGES = {"torch", "tensorflow", "transformers", "opencv-python", "playwright", "selenium"}
EXTERNAL_SERVICE_HINTS = {"openai", "anthropic", "google-generativeai", "boto3", "stripe", "twilio", "slack-sdk"}
HARDWARE_HINTS = {"pyserial", "gpiozero", "rpi.gpio", "smbus2", "sounddevice", "pyaudio"}

PKG_NAME_RE = re.compile(r"^([A-Za-z0-9_.\-]+)\s*([<>=!~].*)?$")


def _parse_req(req: str) -> Tuple[str, str]:
    m = PKG_NAME_RE.match(req.strip())
    if not m:
        return req.strip().lower(), ""
    return m.group(1).lower(), (m.group(2) or "").strip()


class CompatibilityAnalyzer:
    def analyze_single(self, scan: Dict[str, Any], target_arch: str = "arm64") -> Dict[str, Any]:
        manifest = scan.get("manifest") if isinstance(scan.get("manifest"), dict) else {}
        py_deps = scan.get("python_dependencies") or []
        node_deps = (scan.get("node_dependencies") or {}).get("dependencies") or {}

        verified: List[str] = []
        inferred: List[str] = []
        unverified: List[str] = []
        conflicts: List[str] = []
        missing: List[str] = []
        unsupported: List[str] = []
        strategies: List[str] = []

        # Security / archive validity
        if scan.get("security_violations"):
            conflicts.extend(scan["security_violations"])
        if scan.get("integrity_errors"):
            conflicts.extend(scan["integrity_errors"])
        if scan.get("missing_mandatory_files"):
            for mf in scan["missing_mandatory_files"]:
                missing.append(f"Mandatory file missing: {mf}")

        # Backend & Frontend detection
        backend_lang = "Python" if (scan.get("backend_entrypoints") or py_deps) else "Unknown"
        frontend_fw = "React" if "react" in node_deps else ("Static HTML HUD" if scan.get("frontend_entrypoints") else "None detected")

        if scan.get("valid") and manifest:
            verified.append("Archive CRC integrity and path/symlink security checks passed.")
        if manifest.get("compatible_api_version") == "1.0.0":
            inferred.append("Declares JARVIS Common Module Contract v1.0.0 in manifest.json.")
        elif manifest:
            missing.append("manifest.json omits compatible_api_version ('1.0.0').")
        else:
            missing.append("No parseable manifest.json; cannot determine module contract version.")

        # Dependencies, ARM64 compatibility, hardware & external services
        parsed_py = [_parse_req(r) for r in py_deps]
        heavy_found: List[str] = []
        ext_services: List[str] = []
        hw_deps: List[str] = []

        for pkg, spec in parsed_py:
            if target_arch.lower() in {"arm64", "aarch64"} and pkg in ARM64_UNSUPPORTED_OR_RISKY:
                unsupported.append(f"{pkg}{spec}: {ARM64_UNSUPPORTED_OR_RISKY[pkg]}")
            if pkg in HEAVYWEIGHT_PACKAGES:
                heavy_found.append(pkg)
            if pkg in EXTERNAL_SERVICE_HINTS:
                ext_services.append(pkg)
            if pkg in HARDWARE_HINTS:
                hw_deps.append(pkg)

        if target_arch.lower() in {"arm64", "aarch64"} and not unsupported and py_deps:
            inferred.append(
                f"No known x86/Windows/CUDA-only packages detected for target '{target_arch}' "
                f"(host runtime: {platform.machine()}; native wheel availability remains unverified until host install)."
            )

        # DB, WS, Env, Permissions
        db_reqs: List[str] = []
        if any("sqlite" in v.lower() or "db_path" in v.lower() for v in scan.get("env_variables") or []):
            db_reqs.append("SQLite (inferred from env config)")
        if any(p in {"psycopg2", "psycopg2-binary", "asyncpg"} for p, _ in parsed_py):
            db_reqs.append("PostgreSQL")
        if any(p in {"redis"} for p, _ in parsed_py):
            db_reqs.append("Redis")

        permissions = manifest.get("required_permissions") or []
        if not permissions:
            missing.append("required_permissions not declared in manifest.json.")

        # Unverified requirements (never claim runtime compatibility from metadata alone)
        unverified.append("Runtime endpoint behavior and live host mount compatibility are unverified until executed on host.")
        if ext_services:
            unverified.append(f"External service credentials/connectivity unverified for: {', '.join(sorted(ext_services))}.")
        if hw_deps:
            unverified.append(f"Hardware peripheral access unverified for: {', '.join(sorted(hw_deps))}.")

        # Integration strategies
        if heavy_found:
            strategies.append(
                f"Run as an isolated service/process on Raspberry Pi 5 (heavyweight dependencies detected: {', '.join(sorted(heavy_found))})."
            )
        else:
            strategies.append("Eligible for lazy FastAPI router mounting via host mount_module(app) or standalone port binding.")
        if scan.get("env_variables"):
            strategies.append(f"Provision {len(scan['env_variables'])} environment variable(s) before enabling module.")

        return {
            "target_arch": target_arch,
            "host_arch": platform.machine(),
            "summary": {
                "backend_language": backend_lang,
                "frontend_framework": frontend_fw,
                "api_prefixes": scan.get("detected_api_prefixes") or [],
                "ws_routes": scan.get("detected_ws_routes") or [],
                "api_version": manifest.get("compatible_api_version") or "unknown",
                "default_port": (manifest.get("entrypoints") or {}).get("default_port") if isinstance(manifest.get("entrypoints"), dict) else manifest.get("default_port"),
                "python_packages": py_deps,
                "node_packages": list(node_deps.keys()),
                "env_variables": scan.get("env_variables") or [],
                "database_requirements": db_reqs or ["None detected"],
                "required_permissions": permissions,
                "hardware_requirements": hw_deps,
                "external_services": ext_services,
            },
            "verified_compatibility": verified,
            "inferred_from_metadata": inferred,
            "unverified_requirements": unverified,
            "conflicts": conflicts,
            "missing_information": missing,
            "unsupported_dependencies": unsupported,
            "suggested_integration_strategies": strategies,
        }

    def detect_cross_module_conflicts(self, modules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect port collisions, API prefix collisions, and conflicting Python dependency pins across modules."""
        conflicts: List[Dict[str, Any]] = []
        ports: Dict[int, List[str]] = {}
        prefixes: Dict[str, List[str]] = {}
        py_pins: Dict[str, Dict[str, List[str]]] = {}

        for mod in modules:
            mid = mod["module_id"]
            compat = mod.get("compatibility") or {}
            summary = compat.get("summary") or {}

            port = summary.get("default_port")
            if isinstance(port, int):
                ports.setdefault(port, []).append(mid)

            for pref in summary.get("api_prefixes") or []:
                prefixes.setdefault(pref, []).append(mid)

            for req in summary.get("python_packages") or []:
                pkg, spec = _parse_req(req)
                if spec:
                    py_pins.setdefault(pkg, {}).setdefault(spec, []).append(mid)

        for port, mids in ports.items():
            if len(mids) > 1:
                conflicts.append({"type": "PORT_CONFLICT", "detail": f"Port {port} claimed by multiple modules", "modules": mids})

        for pref, mids in prefixes.items():
            if len(mids) > 1:
                conflicts.append({"type": "API_PREFIX_CONFLICT", "detail": f"API prefix '{pref}' claimed by multiple modules", "modules": mids})

        for pkg, spec_map in py_pins.items():
            exact_pins = [s for s in spec_map.keys() if s.startswith("==")]
            if len(exact_pins) > 1:
                involved = sorted({m for s in exact_pins for m in spec_map[s]})
                conflicts.append(
                    {
                        "type": "DEPENDENCY_VERSION_CONFLICT",
                        "package": pkg,
                        "detail": f"Conflicting exact pins for '{pkg}': {', '.join(sorted(exact_pins))}",
                        "modules": involved,
                    }
                )

        return conflicts
