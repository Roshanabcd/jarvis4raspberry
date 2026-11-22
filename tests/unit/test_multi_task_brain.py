"""Tests for JARVIS Multi-Task Brain & Compound Capability Orchestrator."""

from __future__ import annotations

import unittest
from ai.capabilities.multi_task_brain import MultiTaskBrain, get_multi_task_brain


class TestMultiTaskBrain(unittest.TestCase):
    def setUp(self) -> None:
        self.brain = get_multi_task_brain()

    def test_multi_task_detection(self) -> None:
        """Verify multi-task compound prompts are recognized."""
        compound_prompt = "Check system telemetry, run defensive cybersecurity scan on project, and find free slots in my calendar"
        self.assertTrue(self.brain.is_multi_task_request(compound_prompt))

        single_prompt = "What is the CPU usage?"
        self.assertFalse(self.brain.is_multi_task_request(single_prompt))

    def test_plan_creation_with_dependencies(self) -> None:
        """Verify plan creation creates steps and detects dependencies."""
        prompt = "Summarize this youtube video: https://www.youtube.com/watch?v=12345, and then search documents for it"
        plan = self.brain.create_plan(prompt, user_role="USER")
        self.assertEqual(len(plan.steps), 2)
        self.assertEqual(plan.steps[0].capability_id, "youtube-summarizer")
        self.assertEqual(plan.steps[1].capability_id, "document-qa")
        # Step 2 references "it", so it should depend on step 1
        self.assertIn("step_1", plan.steps[1].depends_on)

    def test_execute_multi_task_plan(self) -> None:
        """Verify executing a compound plan completes all steps and produces synthesis."""
        prompt = "Check system telemetry and find free calendar slots for tomorrow"
        plan = self.brain.create_plan(prompt, user_role="USER")
        self.assertEqual(len(plan.steps), 2)

        progress_events = []
        def on_prog(e):
            progress_events.append(e)

        executed = self.brain.execute_plan(plan, user_role="USER", on_progress=on_prog)
        self.assertEqual(executed.status, "completed")
        self.assertEqual(len(progress_events), 2)
        self.assertIn("JARVIS Multi-Task Execution Report", executed.final_summary)
        self.assertTrue(executed.total_execution_time_ms > 0)
        self.assertIn("I completed all 2 tasks", executed.spoken_summary)


if __name__ == "__main__":
    unittest.main()
