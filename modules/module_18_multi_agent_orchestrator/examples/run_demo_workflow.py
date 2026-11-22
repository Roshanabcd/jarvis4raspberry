"""Standalone CLI demo: runs a 4-stage parallel DAG with human approval & aggregation."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.module_18_multi_agent_orchestrator.backend.app.config import OrchestratorConfig
from modules.module_18_multi_agent_orchestrator.backend.services.orchestrator import MultiAgentOrchestrator


async def main() -> None:
    cfg = OrchestratorConfig(db_path=":memory:", max_concurrency=4, poll_interval_sec=0.03)
    orch = MultiAgentOrchestrator(config=cfg)
    await orch.start()
    try:
        wf = "demo-cli-workflow"
        t1 = await orch.submit_task(
            {
                "title": "Research Edge Constraints",
                "workflow_id": wf,
                "required_capability": "research",
                "priority": 3,
                "payload": {"topic": "Pi 5 Concurrency", "delay_sec": 0.05},
            }
        )
        t2 = await orch.submit_task(
            {
                "title": "Static Audit Worker",
                "workflow_id": wf,
                "required_capability": "code_analysis",
                "priority": 3,
                "payload": {"code": "def ok():\n    return True\n", "delay_sec": 0.05},
            }
        )
        t3 = await orch.submit_task(
            {
                "title": "Aggregate Results",
                "workflow_id": wf,
                "required_capability": "aggregation",
                "priority": 4,
                "depends_on": [t1["task_id"], t2["task_id"]],
                "payload": {"numbers": [10, 20, 30], "delay_sec": 0.03},
            }
        )
        t4 = await orch.submit_task(
            {
                "title": "Gated Simulated Release",
                "workflow_id": wf,
                "required_capability": "deploy",
                "priority": 4,
                "depends_on": [t3["task_id"]],
                "requires_approval": True,
                "approval_prompt": "Approve simulated release?",
                "payload": {"target": "sandbox-staging", "delay_sec": 0.03},
            }
        )

        # Wait for t4 to enter awaiting_approval
        for _ in range(100):
            cur = orch.db.get_task(t4["task_id"])
            if cur and cur["status"] == "awaiting_approval":
                break
            await asyncio.sleep(0.03)

        approvals = orch.db.list_approvals(status="pending")
        print(f"Pending approval checkpoint: {approvals[0]['approval_id']} -> approving...")
        await orch.decide_approval(approvals[0]["approval_id"], approved=True, decided_by="demo-cli")

        for _ in range(100):
            cur = orch.db.get_task(t4["task_id"])
            if cur and cur["status"] == "completed":
                break
            await asyncio.sleep(0.03)

        agg = await orch.get_workflow_aggregation(wf)
        print(json.dumps(agg, indent=2))
    finally:
        await orch.stop()
        orch.db.close()


if __name__ == "__main__":
    asyncio.run(main())
