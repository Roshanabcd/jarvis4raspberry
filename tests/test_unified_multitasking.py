"""Integration test for JARVIS Unified Multitasking & Cross-Module Orchestration (Phase 7).

Simulates the instruction:
"Jarvis, inspect my project, run tests, check security issues, create documentation, and give me a summary."
"""

from __future__ import annotations

import asyncio
import unittest
from typing import Any, Dict

from modules.module_18_multi_agent_orchestrator.backend.models.schemas import TaskPriority, TaskStatus
from modules.module_18_multi_agent_orchestrator.backend.services.orchestrator import MultiAgentOrchestrator
from modules.module_22_intelligent_model_router.backend.services.router_engine import IntelligentModelRouterEngine
from modules.module_40_permissions_approval_center.backend.services.approval_engine import ApprovalEngine
from modules.module_41_universal_notification_center.backend.services.notification_engine import NotificationEngine
from modules.module_42_unified_extension_manager.backend.services.extension_manager import ExtensionManager


class TestUnifiedMultitasking(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.orchestrator = MultiAgentOrchestrator()
        self.approvals = ApprovalEngine()
        self.notifications = NotificationEngine()
        self.model_router = IntelligentModelRouterEngine()
        self.extensions = ExtensionManager()

        await self.orchestrator.start()

    async def asyncTearDown(self) -> None:
        await self.orchestrator.stop()
        self.orchestrator.db.close()
        self.model_router.db.close()
        self.extensions.db.close()

    async def test_end_to_end_multitask_workflow(self) -> None:
        """Execute a coordinated multi-module DAG plan across independent & dependent tasks."""
        # 1. Step 1: Permission policy pre-flight check via Module 40
        req = self.approvals.submit_request({
            "module_id": "orchestrator",
            "action": "execute_project_audit",
            "risk_level": "medium",
            "summary": "Multi-agent project audit approval",
            "requester": "jarvis_user",
        })
        self.assertIn("request_id", req)
        
        # Approve request if pending
        if req["status"] == "pending":
            decision = self.approvals.decide_request(
                request_id=req["request_id"],
                decision="approve",
                reviewer="admin",
                rationale="Authorized by human-in-the-loop governance policy",
            )
            self.assertEqual(decision["status"], "approved")

        # 2. Step 2: Model route selection via Module 22
        route_decision = self.model_router.route_request(
            prompt="Analyze project security and generate audit summary",
            task_type="code_generation",
            strategy="balanced",
        )
        self.assertIn("selected_model_id", route_decision)

        # 3. Step 3: Create tasks in DAG
        # Task A: Project Inspection (Independent)
        task_a = await self.orchestrator.submit_task({
            "title": "Inspect project structure",
            "assigned_agent_id": "agent-code-01",
            "priority": TaskPriority.HIGH.value,
            "payload": {"code": "import os\ndef audit():\n    return {'files': 42}\n"},
        })

        # Task B: Security Scan (Independent)
        task_b = await self.orchestrator.submit_task({
            "title": "Run defensive security scan",
            "assigned_agent_id": "agent-code-01",
            "priority": TaskPriority.HIGH.value,
            "payload": {"code": "# Safe security rules\nimport hashlib\nh = hashlib.sha256()\n"},
        })

        # Task C: Summary Aggregator (Dependent on A and B)
        task_c = await self.orchestrator.submit_task({
            "title": "Aggregate results & produce executive summary",
            "assigned_agent_id": "agent-aggregator-01",
            "priority": TaskPriority.NORMAL.value,
            "depends_on": [task_a["task_id"], task_b["task_id"]],
            "payload": {"numbers": [10.0, 20.0, 30.0]},
        })

        # 4. Wait for DAG completion
        completed = False
        for _ in range(60):
            await asyncio.sleep(0.1)
            status_c = self.orchestrator.db.get_task(task_c["task_id"])
            if status_c and status_c["status"] == TaskStatus.COMPLETED.value:
                completed = True
                break

        self.assertTrue(completed, "Task C should complete once dependencies A and B finish")

        # 5. Verify results in DAG
        result_a = self.orchestrator.db.get_task(task_a["task_id"])
        result_b = self.orchestrator.db.get_task(task_b["task_id"])
        result_c = self.orchestrator.db.get_task(task_c["task_id"])

        self.assertEqual(result_a["status"], TaskStatus.COMPLETED.value)
        self.assertEqual(result_b["status"], TaskStatus.COMPLETED.value)
        self.assertEqual(result_c["status"], TaskStatus.COMPLETED.value)

        aggregated_tasks = result_c["result"].get("aggregated_from_tasks", [])
        self.assertIn(task_a["task_id"], aggregated_tasks)
        self.assertIn(task_b["task_id"], aggregated_tasks)

        # 6. Step 6: Dispatch notification via Module 41
        notif = self.notifications.send_notification({
            "source_module": "orchestrator",
            "title": "Project Audit Complete",
            "message": f"Multitasking workflow completed successfully. Processed tasks: {task_a['task_id']}, {task_b['task_id']}, {task_c['task_id']}",
            "channels": ["hud"],
            "priority": "normal",
        })
        self.assertIn(notif["status"], ["unread", "delivered"])

        # 7. Step 7: Verify extension manager tracks registered modules
        ext_list = self.extensions.db.list_modules()
        self.assertIsInstance(ext_list, list)


if __name__ == "__main__":
    unittest.main()
