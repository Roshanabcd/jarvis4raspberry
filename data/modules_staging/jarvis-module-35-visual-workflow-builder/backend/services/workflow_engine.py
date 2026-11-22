"""Visual Workflow Builder DAG Validation & Topological Execution Engine (Module 35)."""

from __future__ import annotations

import time
import uuid
from collections import deque
from typing import Any, Dict, List, Optional, Set

from backend.app.config import WorkflowConfig
from backend.models.database import WorkflowDB, utc_now_iso


class WorkflowError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def _eval_condition(actual: Any, op: str, expected: Any) -> bool:
    if op == "==":
        return actual == expected
    if op == "!=":
        return actual != expected
    if op == "contains":
        return str(expected) in str(actual)
    lhs, rhs = float(actual), float(expected)
    if op == ">":
        return lhs > rhs
    if op == ">=":
        return lhs >= rhs
    if op == "<":
        return lhs < rhs
    if op == "<=":
        return lhs <= rhs
    return False


class WorkflowEngine:
    adapter_name: str = "local_dag_workflow_engine"
    is_simulated: bool = False

    def __init__(
        self,
        config: Optional[WorkflowConfig] = None,
        db: Optional[WorkflowDB] = None,
    ) -> None:
        self.config = config or WorkflowConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or WorkflowDB(self.config.db_path)
        self._started_at = time.monotonic()

    def validate_dag(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> List[str]:
        node_ids = [n["node_id"] for n in nodes]
        if len(node_ids) != len(set(node_ids)):
            raise WorkflowError("DUPLICATE_NODE_ID", "Workflow contains duplicate node_id values.", 422)
        node_set = set(node_ids)

        adj: Dict[str, List[str]] = {nid: [] for nid in node_ids}
        indeg: Dict[str, int] = {nid: 0 for nid in node_ids}

        for edge in edges:
            src, dst = edge["source"], edge["target"]
            if src not in node_set or dst not in node_set:
                raise WorkflowError(
                    "INVALID_EDGE_REFERENCE",
                    f"Edge ({src} -> {dst}) references an unknown node_id.",
                    422,
                )
            if src == dst:
                raise WorkflowError("WORKFLOW_CYCLE_DETECTED", f"Self-loop detected on node '{src}'.", 422)
            adj[src].append(dst)
            indeg[dst] += 1

        q: deque[str] = deque(nid for nid in node_ids if indeg[nid] == 0)
        order: List[str] = []
        while q:
            u = q.popleft()
            order.append(u)
            for v in adj[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    q.append(v)

        if len(order) != len(node_ids):
            raise WorkflowError(
                "WORKFLOW_CYCLE_DETECTED",
                "Workflow graph contains a cycle and cannot be topologically executed.",
                422,
            )
        return order

    def create_workflow(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        order = self.validate_dag(payload["nodes"], payload.get("edges", []))
        wf = self.db.create_workflow(
            {
                "workflow_id": f"wfl_{uuid.uuid4().hex[:10]}",
                "name": payload["name"].strip(),
                "description": payload.get("description", "").strip(),
                "nodes": payload["nodes"],
                "edges": payload.get("edges", []),
                "created_at": utc_now_iso(),
            }
        )
        out = dict(wf)
        out["execution_order"] = order
        return out

    def validate_workflow_by_id(self, workflow_id: str) -> Dict[str, Any]:
        wf = self.db.get_workflow(workflow_id)
        if not wf:
            raise WorkflowError("WORKFLOW_NOT_FOUND", f"Workflow '{workflow_id}' not found.", 404)
        order = self.validate_dag(wf["nodes"], wf["edges"])
        return {"workflow_id": workflow_id, "valid": True, "execution_order": order}

    def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        wf = self.db.get_workflow(workflow_id)
        if not wf:
            raise WorkflowError("WORKFLOW_NOT_FOUND", f"Workflow '{workflow_id}' not found.", 404)
        order = self.validate_dag(wf["nodes"], wf["edges"])
        node_map = {n["node_id"]: n for n in wf["nodes"]}
        parents: Dict[str, List[str]] = {n["node_id"]: [] for n in wf["nodes"]}
        for e in wf["edges"]:
            parents[e["target"]].append(e["source"])

        context: Dict[str, Any] = dict(input_data or {})
        trace: List[Dict[str, Any]] = []
        blocked_nodes: Set[str] = set()

        for nid in order:
            node = node_map[nid]
            t0 = time.monotonic()
            # If any parent condition failed or was skipped, skip downstream branch
            if any(p in blocked_nodes for p in parents[nid]):
                blocked_nodes.add(nid)
                trace.append(
                    {
                        "node_id": nid,
                        "node_type": node["node_type"],
                        "status": "skipped",
                        "duration_ms": 0.0,
                        "output": {"reason": "upstream condition not met"},
                    }
                )
                continue

            cfg = node.get("config", {})
            ntype = node["node_type"]
            output: Dict[str, Any] = {}

            if ntype == "trigger":
                output = {"triggered": True, "keys": sorted(context.keys())}
            elif ntype == "transform":
                out_key = cfg.get("output_key", "transformed")
                op = cfg.get("operation", "template")
                if op == "uppercase":
                    val = str(context.get(cfg.get("input_key", ""), "")).upper()
                elif op == "lowercase":
                    val = str(context.get(cfg.get("input_key", ""), "")).lower()
                else:
                    tmpl = str(cfg.get("template", ""))
                    val = tmpl.format_map({k: v for k, v in context.items()})
                context[out_key] = val
                output = {out_key: val}
            elif ntype == "math":
                out_key = cfg.get("output_key", "result")
                a = float(context.get(cfg.get("a_key", ""), cfg.get("a", 0.0)))
                b = float(context.get(cfg.get("b_key", ""), cfg.get("b", 0.0)))
                op = cfg.get("operation", "add")
                if op == "sub":
                    res = a - b
                elif op == "mul":
                    res = a * b
                elif op == "div":
                    res = (a / b) if b != 0 else 0.0
                else:
                    res = a + b
                res = round(res, 4)
                context[out_key] = res
                output = {out_key: res}
            elif ntype == "condition":
                actual = context.get(cfg.get("input_key", ""))
                passed = _eval_condition(actual, cfg.get("operator", "=="), cfg.get("value"))
                output = {"passed": passed}
                if not passed:
                    blocked_nodes.add(nid)
            elif ntype == "notify":
                msg = str(cfg.get("message", "Workflow notification")).format_map({k: v for k, v in context.items()})
                notifications = list(context.get("_notifications", []))
                notifications.append(msg)
                context["_notifications"] = notifications
                output = {"notified": msg}

            dur_ms = round((time.monotonic() - t0) * 1000.0, 3)
            trace.append(
                {
                    "node_id": nid,
                    "node_type": ntype,
                    "status": "completed",
                    "duration_ms": dur_ms,
                    "output": output,
                }
            )

        run = self.db.add_run(
            {
                "run_id": f"run_{uuid.uuid4().hex[:10]}",
                "workflow_id": workflow_id,
                "status": "completed",
                "input_data": input_data,
                "final_context": context,
                "trace": trace,
                "created_at": utc_now_iso(),
            }
        )
        return run

    def get_status(self) -> Dict[str, Any]:
        return {
            "adapter": self.adapter_name,
            "simulated": self.is_simulated,
            "workflows_count": len(self.db.list_workflows()),
            "runs_count": len(self.db.list_runs(limit=500)),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
