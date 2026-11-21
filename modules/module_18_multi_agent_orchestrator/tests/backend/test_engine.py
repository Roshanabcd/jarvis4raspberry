"""Backend unit & async orchestration tests for JARVIS Module 18 (unittest & pytest compatible)."""

from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from modules.module_18_multi_agent_orchestrator.backend.app.config import OrchestratorConfig
from modules.module_18_multi_agent_orchestrator.backend.services.orchestrator import MultiAgentOrchestrator, OrchestratorError


async def wait_until(predicate, timeout: float = 4.0, step: float = 0.02) -> bool:
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        if predicate():
            return True
        await asyncio.sleep(step)
    return False


class TestOrchestratorEngine(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self._tmp.name) / "test_orch.db")
        self.config = OrchestratorConfig(
            db_path=self.db_path,
            max_concurrency=3,
            default_timeout_sec=5.0,
            poll_interval_sec=0.02,
        )
        self.orch = MultiAgentOrchestrator(config=self.config)
        await self.orch.start()

    async def asyncTearDown(self) -> None:
        await self.orch.stop()
        self.orch.db.close()
        self._tmp.cleanup()

    async def test_dag_dependency_execution_and_result_aggregation(self) -> None:
        wf = "wf-dag-01"
        t1 = await self.orch.submit_task(
            {
                "title": "Branch A Research",
                "workflow_id": wf,
                "required_capability": "research",
                "payload": {"topic": "Branch A", "delay_sec": 0.04},
            }
        )
        t2 = await self.orch.submit_task(
            {
                "title": "Branch B Audit",
                "workflow_id": wf,
                "required_capability": "code_analysis",
                "payload": {"code": "x = eval('1+1')", "delay_sec": 0.04},
            }
        )
        t3 = await self.orch.submit_task(
            {
                "title": "Merge Results",
                "workflow_id": wf,
                "required_capability": "aggregation",
                "depends_on": [t1["task_id"], t2["task_id"]],
                "payload": {"numbers": [2, 4, 6], "delay_sec": 0.02},
            }
        )

        done = await wait_until(lambda: (self.orch.db.get_task(t3["task_id"]) or {}).get("status") == "completed")
        self.assertTrue(done, "Downstream aggregation task did not complete in time")

        final = self.orch.db.get_task(t3["task_id"])
        assert final is not None
        self.assertEqual(final["result"]["upstream_count"], 2)
        self.assertEqual(final["result"]["numeric_stats"]["mean"], 4.0)

        t2_done = self.orch.db.get_task(t2["task_id"])
        assert t2_done is not None
        self.assertEqual(t2_done["result"]["risk_level"], "HIGH")
        self.assertIn("eval(", t2_done["result"]["risky_patterns_detected"])

        agg = await self.orch.get_workflow_aggregation(wf)
        self.assertEqual(agg["status"], "completed")
        self.assertEqual(agg["progress_percent"], 100.0)
        self.assertEqual(len(agg["aggregated_results"]), 3)

    async def test_missing_dependency_rejected(self) -> None:
        with self.assertRaises(OrchestratorError) as ctx:
            await self.orch.submit_task({"title": "Bad Dep", "depends_on": ["tsk_nonexistent"]})
        self.assertEqual(ctx.exception.code, "DEPENDENCY_NOT_FOUND")

    async def test_priority_scheduling_order(self) -> None:
        await self.orch.pause_engine()
        await self.orch.set_max_concurrency(1)
        order: list[str] = []

        async def record_handler(task, _ctx):
            order.append(task["title"])
            await asyncio.sleep(0.02)
            return {"ok": True}

        self.orch.register_handler("order_test", record_handler)
        await self.orch.register_agent(
            {
                "agent_id": "agent-order",
                "name": "Order Agent",
                "role": "Tester",
                "capabilities": ["order_test"],
                "max_concurrency": 1,
                "handler_type": "order_test",
            }
        )

        await self.orch.submit_task({"title": "LOW", "priority": 1, "required_capability": "order_test"})
        await self.orch.submit_task({"title": "CRITICAL", "priority": 4, "required_capability": "order_test"})
        await self.orch.submit_task({"title": "HIGH", "priority": 3, "required_capability": "order_test"})

        await self.orch.resume_engine()
        done = await wait_until(lambda: len(order) == 3)
        self.assertTrue(done)
        self.assertEqual(order, ["CRITICAL", "HIGH", "LOW"])

    async def test_bounded_concurrency_limit_enforced(self) -> None:
        await self.orch.set_max_concurrency(2)
        active = 0
        peak = 0

        async def slow_handler(_task, _ctx):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0.08)
            active -= 1
            return {"ok": True}

        self.orch.register_handler("conc_test", slow_handler)
        await self.orch.register_agent(
            {
                "agent_id": "agent-conc",
                "name": "Conc Agent",
                "role": "Worker",
                "capabilities": ["conc_test"],
                "max_concurrency": 5,
                "handler_type": "conc_test",
            }
        )

        ids = []
        for i in range(4):
            t = await self.orch.submit_task({"title": f"Parallel {i}", "required_capability": "conc_test"})
            ids.append(t["task_id"])

        done = await wait_until(
            lambda: all((self.orch.db.get_task(tid) or {}).get("status") == "completed" for tid in ids)
        )
        self.assertTrue(done)
        self.assertEqual(peak, 2)

    async def test_retry_with_backoff_and_timeout(self) -> None:
        await self.orch.register_agent(
            {
                "agent_id": "agent-flaky",
                "name": "Flaky Worker",
                "role": "Retry Tester",
                "capabilities": ["flaky_test"],
                "max_concurrency": 2,
                "handler_type": "flaky_test",
            }
        )

        # Succeeds on 2nd attempt
        t_ok = await self.orch.submit_task(
            {
                "title": "Transient Flaky Task",
                "required_capability": "flaky_test",
                "max_retries": 2,
                "retry_backoff_sec": 0.03,
                "timeout_sec": 2.0,
                "payload": {"fail_times": 1, "sleep_sec": 0.01},
            }
        )
        # Times out permanently
        t_to = await self.orch.submit_task(
            {
                "title": "Timeout Task",
                "required_capability": "flaky_test",
                "max_retries": 0,
                "timeout_sec": 0.1,
                "payload": {"fail_times": 0, "sleep_sec": 0.4},
            }
        )

        done = await wait_until(
            lambda: (self.orch.db.get_task(t_ok["task_id"]) or {}).get("status") == "completed"
            and (self.orch.db.get_task(t_to["task_id"]) or {}).get("status") == "failed"
        )
        self.assertTrue(done)
        ok_rec = self.orch.db.get_task(t_ok["task_id"])
        to_rec = self.orch.db.get_task(t_to["task_id"])
        assert ok_rec and to_rec
        self.assertEqual(ok_rec["retries_attempted"], 1)
        self.assertIn("Timeout", to_rec["error"])

    async def test_human_approval_approve_and_reject_cascade(self) -> None:
        # 1. Approval granted
        t_app = await self.orch.submit_task(
            {
                "title": "Gated Action Approved",
                "required_capability": "deploy",
                "requires_approval": True,
                "approval_prompt": "Approve test action?",
                "payload": {"target": "sandbox", "delay_sec": 0.02},
            }
        )
        self.assertEqual(t_app["status"], "awaiting_approval")
        apr = self.orch.db.get_approval_by_task(t_app["task_id"])
        assert apr is not None
        await self.orch.decide_approval(apr["approval_id"], approved=True, decided_by="roshan")
        done = await wait_until(lambda: (self.orch.db.get_task(t_app["task_id"]) or {}).get("status") == "completed")
        self.assertTrue(done)

        # 2. Approval rejected cascades to dependent
        t_rej = await self.orch.submit_task(
            {
                "title": "Gated Action Rejected",
                "required_capability": "deploy",
                "requires_approval": True,
            }
        )
        t_child = await self.orch.submit_task(
            {
                "title": "Downstream Dependent",
                "required_capability": "research",
                "depends_on": [t_rej["task_id"]],
            }
        )
        apr2 = self.orch.db.get_approval_by_task(t_rej["task_id"])
        assert apr2 is not None
        await self.orch.decide_approval(apr2["approval_id"], approved=False, decided_by="roshan", comment="Denied")
        self.assertEqual((self.orch.db.get_task(t_rej["task_id"]) or {}).get("status"), "cancelled")
        self.assertEqual((self.orch.db.get_task(t_child["task_id"]) or {}).get("status"), "cancelled")

    async def test_pause_resume_and_cancel_task(self) -> None:
        await self.orch.pause_engine()
        t = await self.orch.submit_task({"title": "Controllable Task", "required_capability": "research"})
        paused = await self.orch.pause_task(t["task_id"])
        self.assertEqual(paused["status"], "paused")
        resumed = await self.orch.resume_task(t["task_id"])
        self.assertEqual(resumed["status"], "queued")
        cancelled = await self.orch.cancel_task(t["task_id"])
        self.assertEqual(cancelled["status"], "cancelled")


if __name__ == "__main__":
    unittest.main()
