"""Dry-Run Installation Planner for JARVIS Module 42.

Produces dependency-ordered installation plans, conflict checks, permission summaries,
required configuration checklists, and rollback instructions. Never executes install
scripts automatically; requires explicit operator approval.
"""

from __future__ import annotations

from typing import Any, Dict, List, Set

from backend.services.compatibility_analyzer import CompatibilityAnalyzer


class InstallationPlanner:
    def __init__(self, analyzer: CompatibilityAnalyzer) -> None:
        self.analyzer = analyzer

    def build_plan(self, modules: List[Dict[str, Any]], selected_ids: List[str] | None = None) -> Dict[str, Any]:
        by_id = {m["module_id"]: m for m in modules}
        target_ids = selected_ids if selected_ids else list(by_id.keys())
        target_mods = [by_id[mid] for mid in target_ids if mid in by_id]
        missing_targets = [mid for mid in target_ids if mid not in by_id]

        # Topological sort of jarvis_modules dependencies
        visited: Set[str] = set()
        visiting: Set[str] = set()
        ordered: List[str] = []
        cycles: List[str] = []
        missing_deps: List[Dict[str, str]] = []

        def dfs(mid: str) -> None:
            if mid in visited:
                return
            if mid in visiting:
                cycles.append(f"Cyclic module dependency detected involving '{mid}'.")
                return
            visiting.add(mid)
            mod = by_id.get(mid)
            if mod:
                deps = (mod.get("dependencies") or {}).get("jarvis_modules") or []
                for dep_id in deps:
                    if dep_id not in by_id:
                        missing_deps.append({"module_id": mid, "missing_dependency": dep_id})
                    else:
                        dfs(dep_id)
            visiting.remove(mid)
            visited.add(mid)
            if mid in by_id:
                ordered.append(mid)

        for mid in [m["module_id"] for m in target_mods]:
            dfs(mid)

        cross_conflicts = self.analyzer.detect_cross_module_conflicts(target_mods)
        permissions: Set[str] = set()
        required_env: Set[str] = set()
        steps: List[Dict[str, Any]] = []

        for idx, mid in enumerate(ordered, start=1):
            mod = by_id[mid]
            compat = mod.get("compatibility") or {}
            summary = compat.get("summary") or {}
            for p in mod.get("required_permissions") or []:
                permissions.add(str(p))
            for env_k in summary.get("env_variables") or []:
                required_env.add(str(env_k))
            steps.append(
                {
                    "order": idx,
                    "module_id": mid,
                    "name": mod["name"],
                    "version": mod["version"],
                    "source_archive": mod.get("source_archive"),
                    "strategy": (compat.get("suggested_integration_strategies") or ["Lazy router mount"])[0],
                    "requires_explicit_approval": True,
                }
            )

        rollback_instructions = [
            "1. Disable newly added module(s) via POST /api/v1/extensions/modules/{module_id}/toggle with {\"enabled\": false}.",
            "2. Remove the extracted module directory from the target extensions path.",
            "3. Restore the previous SQLite registry backup and host router configuration.",
            "4. Restart the JARVIS host process and verify /api/v1/extensions/health returns 200 OK.",
        ]

        return {
            "dry_run": True,
            "auto_execute": False,
            "approval_required": True,
            "install_order": steps,
            "missing_targets": missing_targets,
            "missing_dependencies": missing_deps,
            "dependency_cycles": cycles,
            "conflicts": cross_conflicts,
            "permission_summary": sorted(permissions),
            "required_configuration": sorted(required_env),
            "rollback_instructions": rollback_instructions,
            "ready_for_approval": len(missing_targets) == 0 and len(missing_deps) == 0 and len(cycles) == 0 and len(cross_conflicts) == 0,
        }
