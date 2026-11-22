"""Tests for JARVIS Autonomous Capability Router."""

from __future__ import annotations

import unittest
from ai.capabilities.router import AutonomousCapabilityRouter, get_capability_router


class TestCapabilityRouter(unittest.TestCase):
    def setUp(self) -> None:
        self.router = get_capability_router()

    def test_route_developer_clis(self) -> None:
        """Verify routing for all developer coding CLIs."""
        cases = [
            ("ask Claude to diagnose repository and find bug", "developer-cli:claude", "diagnose"),
            ("run Antigravity on test suite", "developer-cli:antigravity", "run_task"),
            ("use Codex to generate authentication API", "developer-cli:codex", "run_task"),
            ("run Copilot to suggest optimizations", "developer-cli:copilot", "run_task"),
            ("ask Hermes to refactor database models", "developer-cli:hermes", "run_task"),
            ("run Aider on backend code", "developer-cli:aider", "run_task"),
            ("run OpenCode to fix syntax errors", "developer-cli:opencode", "run_task"),
            ("run Cline to run project tests", "developer-cli:cline", "run_task"),
        ]
        for prompt, expected_cap, expected_act in cases:
            match = self.router.route(prompt)
            self.assertIsNotNone(match, f"Prompt '{prompt}' should route to capability")
            self.assertEqual(match.capability_id, expected_cap)
            self.assertEqual(match.action_id, expected_act)
            self.assertGreaterEqual(match.confidence, 0.85)
            self.assertIn("prompt", match.extracted_parameters)

    def test_route_core_apps(self) -> None:
        """Verify routing for canonical core apps."""
        # YouTube
        yt_prompt = "Jarvis, summarize this youtube video: https://www.youtube.com/watch?v=abc123xyz"
        yt_match = self.router.route(yt_prompt)
        self.assertIsNotNone(yt_match)
        self.assertEqual(yt_match.capability_id, "youtube-summarizer")
        self.assertEqual(yt_match.extracted_parameters.get("url"), "https://www.youtube.com/watch?v=abc123xyz")

        # Document QA
        doc_prompt = "Search documents for company travel expense policy"
        doc_match = self.router.route(doc_prompt)
        self.assertIsNotNone(doc_match)
        self.assertEqual(doc_match.capability_id, "document-qa")
        self.assertEqual(doc_match.action_id, "query_documents")
        self.assertIn("company travel expense policy", doc_match.extracted_parameters.get("query", ""))

        # Research Assistant
        res_prompt = "Perform research on neuromorphic computing architectures"
        res_match = self.router.route(res_prompt)
        self.assertIsNotNone(res_match)
        self.assertEqual(res_match.capability_id, "research-assistant")
        self.assertIn("neuromorphic computing", res_match.extracted_parameters.get("topic", ""))

        # System Telemetry
        sys_prompt = "Display system telemetry status and CPU temperature"
        sys_match = self.router.route(sys_prompt)
        self.assertIsNotNone(sys_match)
        self.assertEqual(sys_match.capability_id, "system-telemetry")

        # Desktop PC Tools
        dt_prompt = "Open VS Code on my desktop"
        dt_match = self.router.route(dt_prompt)
        self.assertIsNotNone(dt_match)
        self.assertEqual(dt_match.capability_id, "desktop-pc-tools")
        self.assertEqual(dt_match.extracted_parameters.get("app_name"), "vs code")

    def test_route_extension_modules(self) -> None:
        """Verify routing for extension modules."""
        # Module 24: Email & Calendar
        cal_prompt = "Check my calendar and find free slots for tomorrow"
        cal_match = self.router.route(cal_prompt)
        self.assertIsNotNone(cal_match)
        self.assertEqual(cal_match.capability_id, "module:24:email_calendar_assistant")

        # Module 30: Smart Home
        sh_prompt = "Turn on the living room light with smart home"
        sh_match = self.router.route(sh_prompt)
        self.assertIsNotNone(sh_match)
        self.assertEqual(sh_match.capability_id, "module:30:smart_home_controller")

        # Module 33: Defensive Cybersecurity
        sec_prompt = "Run defensive cybersecurity scan on the repository"
        sec_match = self.router.route(sec_prompt)
        self.assertIsNotNone(sec_match)
        self.assertEqual(sec_match.capability_id, "module:33:defensive_cybersecurity_agent")

    def test_unmatched_fallback(self) -> None:
        """Verify that open-ended chat prompts gracefully return None for LLM handling."""
        unmatched_prompts = [
            "What is the capital of France?",
            "Tell me a bedtime story about robots",
            "How does photosynthesis work?",
            "Write a poem about the ocean",
        ]
        for p in unmatched_prompts:
            match = self.router.route(p)
            self.assertIsNone(match, f"Prompt '{p}' should not trigger an autonomous capability")


if __name__ == "__main__":
    unittest.main()
