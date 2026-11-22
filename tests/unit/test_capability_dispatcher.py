"""Tests for JARVIS Unified Capability Dispatcher."""

from __future__ import annotations

import unittest
from ai.capabilities.dispatcher import get_capability_dispatcher
from ai.capabilities.models import CapabilityInvocationRequest


class TestCapabilityDispatcher(unittest.TestCase):
    def setUp(self) -> None:
        self.dispatcher = get_capability_dispatcher()

    def test_dispatch_system_telemetry(self) -> None:
        """Verify executing system-telemetry returns ok status and hardware stats."""
        req = CapabilityInvocationRequest(
            capability_id="system-telemetry",
            action_id="get_status",
            role="USER",
        )
        res = self.dispatcher.execute(req)
        self.assertEqual(res.status, "ok")
        self.assertIn("System Telemetry", res.markdown_output)
        self.assertTrue(len(res.spoken_summary) > 0)
        self.assertIn("system", res.data)

    def test_dispatch_document_qa(self) -> None:
        """Verify executing document-qa search."""
        req = CapabilityInvocationRequest(
            capability_id="document-qa",
            action_id="query_documents",
            parameters={"query": "test policy query", "top_k": 3},
            role="USER",
        )
        res = self.dispatcher.execute(req)
        self.assertEqual(res.status, "ok")
        self.assertIn("Document QA", res.markdown_output)

    def test_dispatch_youtube_without_url(self) -> None:
        """Verify youtube summarizer returns error when no URL or player active."""
        req = CapabilityInvocationRequest(
            capability_id="youtube-summarizer",
            action_id="summarize_video",
            parameters={},
            role="USER",
        )
        res = self.dispatcher.execute(req)
        self.assertEqual(res.status, "error")
        self.assertIn("Please provide", res.spoken_summary)

    def test_dispatch_module_24_calendar(self) -> None:
        """Verify executing Module 24 Email & Calendar Assistant."""
        req = CapabilityInvocationRequest(
            capability_id="module:24:email_calendar_assistant",
            action_id="execute",
            parameters={"instruction": "Find free slots"},
            role="USER",
        )
        res = self.dispatcher.execute(req)
        self.assertEqual(res.status, "ok")
        self.assertIn("Email & Calendar", res.markdown_output)
        self.assertIn("slots", res.data)

    def test_rbac_admin_enforcement(self) -> None:
        """Verify non-admin users cannot execute ADMIN-gated capabilities."""
        req = CapabilityInvocationRequest(
            capability_id="module:33:defensive_cybersecurity_agent",
            action_id="execute",
            role="USER",  # module 33 requires ADMIN
        )
        res = self.dispatcher.execute(req)
        self.assertEqual(res.status, "unauthorized")
        self.assertIn("requires `ADMIN`", res.markdown_output)

        # But ADMIN can execute it
        admin_req = CapabilityInvocationRequest(
            capability_id="module:33:defensive_cybersecurity_agent",
            action_id="execute",
            role="ADMIN",
        )
        admin_res = self.dispatcher.execute(admin_req)
        self.assertEqual(admin_res.status, "ok")

    def test_rbac_guest_enforcement(self) -> None:
        """Verify GUEST users cannot execute operational capabilities."""
        req = CapabilityInvocationRequest(
            capability_id="document-qa",
            action_id="query_documents",
            parameters={"query": "secret docs"},
            role="GUEST",
        )
        res = self.dispatcher.execute(req)
        self.assertEqual(res.status, "unauthorized")
        self.assertIn("Guest operators cannot execute", res.markdown_output)


if __name__ == "__main__":
    unittest.main()
