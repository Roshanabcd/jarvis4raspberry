"""Working reference agent implementations for Module 18.

Each reference agent performs real local async computation and clearly flags
when an external AI/deployment action is running in local simulation mode.
"""

from __future__ import annotations

import asyncio
import hashlib
import math
from typing import Any, Awaitable, Callable, Dict, List

from backend.models.database import utc_now_iso

AgentHandler = Callable[[Dict[str, Any], Dict[str, Any]], Awaitable[Dict[str, Any]]]


async def research_agent_handler(task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Local deterministic research synthesizer (simulated external search)."""
    payload = task.get("payload", {})
    delay = float(payload.get("delay_sec", 0.05))
    if delay > 0:
        await asyncio.sleep(delay)

    topic = str(payload.get("topic") or task.get("title", "general topic"))
    sources = payload.get("sources") or [
        "local-architecture-notes",
        "module-18-contract-v1",
        "dependency-graph-policy",
    ]
    digest = hashlib.sha256(topic.encode("utf-8")).hexdigest()[:12]
    return {
        "simulated": True,
        "agent_type": "research",
        "topic": topic,
        "findings": [
            f"Analyzed '{topic}' across {len(sources)} local reference sources.",
            f"Generated deterministic research fingerprint {digest}.",
        ],
        "sources_reviewed": sources,
        "upstream_dependency_count": len(context.get("dependency_results", {})),
        "completed_at": utc_now_iso(),
    }


async def code_analysis_agent_handler(task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Performs real local static inspection on provided code snippet or metrics."""
    payload = task.get("payload", {})
    delay = float(payload.get("delay_sec", 0.05))
    if delay > 0:
        await asyncio.sleep(delay)

    code = str(payload.get("code", "def health():\n    return {'status': 'ok'}\n"))
    lines = code.splitlines()
    risky_patterns = [
        pat for pat in ("eval(", "exec(", "os.system(", "subprocess.Popen", "shell=True") if pat in code
    ]
    return {
        "simulated": False,
        "agent_type": "code_analysis",
        "line_count": len(lines),
        "char_count": len(code),
        "risky_patterns_detected": risky_patterns,
        "risk_level": "HIGH" if risky_patterns else "LOW",
        "completed_at": utc_now_iso(),
    }


async def data_aggregator_agent_handler(task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Aggregates real outputs from all upstream dependency tasks in the DAG."""
    payload = task.get("payload", {})
    delay = float(payload.get("delay_sec", 0.05))
    if delay > 0:
        await asyncio.sleep(delay)

    dep_results: Dict[str, Any] = context.get("dependency_results", {})
    numbers: List[float] = [float(x) for x in payload.get("numbers", []) if isinstance(x, (int, float))]
    stats = {}
    if numbers:
        mean = sum(numbers) / len(numbers)
        variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
        stats = {
            "count": len(numbers),
            "sum": round(sum(numbers), 4),
            "mean": round(mean, 4),
            "stddev": round(math.sqrt(variance), 4),
            "min": min(numbers),
            "max": max(numbers),
        }

    return {
        "simulated": False,
        "agent_type": "data_aggregator",
        "aggregated_from_tasks": sorted(dep_results.keys()),
        "upstream_count": len(dep_results),
        "upstream_summaries": {
            tid: (res.get("agent_type") if isinstance(res, dict) else str(type(res).__name__))
            for tid, res in dep_results.items()
        },
        "numeric_stats": stats,
        "completed_at": utc_now_iso(),
    }


async def human_gated_deploy_handler(task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Simulated release/action agent that executes only after human approval."""
    payload = task.get("payload", {})
    delay = float(payload.get("delay_sec", 0.05))
    if delay > 0:
        await asyncio.sleep(delay)

    target = str(payload.get("target", "staging-sandbox"))
    return {
        "simulated": True,
        "agent_type": "human_gated_deploy",
        "target": target,
        "approval_verified": True,
        "status": f"[SIMULATED] Executed approved action for '{target}' (no real infrastructure modified).",
        "upstream_inputs": list(context.get("dependency_results", {}).keys()),
        "completed_at": utc_now_iso(),
    }


async def flaky_test_agent_handler(task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Reference agent for verifying retry backoff & timeout handling."""
    payload = task.get("payload", {})
    fail_times = int(payload.get("fail_times", 0))
    sleep_sec = float(payload.get("sleep_sec", 0.02))
    attempt = int(context.get("attempt", 1))

    if sleep_sec > 0:
        await asyncio.sleep(sleep_sec)

    if attempt <= fail_times:
        raise RuntimeError(f"Simulated transient failure on attempt {attempt}/{fail_times}")

    return {
        "simulated": True,
        "agent_type": "flaky_test",
        "succeeded_on_attempt": attempt,
        "completed_at": utc_now_iso(),
    }


REFERENCE_HANDLERS: Dict[str, AgentHandler] = {
    "research": research_agent_handler,
    "code_analysis": code_analysis_agent_handler,
    "data_aggregator": data_aggregator_agent_handler,
    "deploy": human_gated_deploy_handler,
    "flaky_test": flaky_test_agent_handler,
}


DEFAULT_REFERENCE_AGENTS: List[Dict[str, Any]] = [
    {
        "agent_id": "agent-research-01",
        "name": "ARIA Research Synth",
        "role": "Information Synthesis & Planning",
        "capabilities": ["research", "planning", "summarize"],
        "max_concurrency": 2,
        "handler_type": "research",
        "simulated": True,
        "metadata": {"tier": "reference", "simulation_label": "Local deterministic research simulator"},
    },
    {
        "agent_id": "agent-code-01",
        "name": "ATLAS Static Auditor",
        "role": "Code Inspection & Safety Verification",
        "capabilities": ["code_analysis", "security_scan", "lint"],
        "max_concurrency": 2,
        "handler_type": "code_analysis",
        "simulated": False,
        "metadata": {"tier": "reference", "simulation_label": "Real local static pattern analyzer"},
    },
    {
        "agent_id": "agent-aggregator-01",
        "name": "NEXUS Result Aggregator",
        "role": "Multi-Agent Output Aggregation & Metrics",
        "capabilities": ["aggregation", "analytics", "reporting"],
        "max_concurrency": 2,
        "handler_type": "data_aggregator",
        "simulated": False,
        "metadata": {"tier": "reference", "simulation_label": "Real local DAG result aggregator"},
    },
    {
        "agent_id": "agent-deploy-01",
        "name": "AEGIS Gated Executor",
        "role": "Human-Approved Action Execution",
        "capabilities": ["deploy", "release", "gated_action"],
        "max_concurrency": 1,
        "handler_type": "deploy",
        "simulated": True,
        "metadata": {"tier": "reference", "simulation_label": "Simulated deployment executor (requires approval)"},
    },
]
