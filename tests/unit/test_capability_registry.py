"""Tests for JARVIS Unified Capability Registry."""

from __future__ import annotations

import unittest
from ai.capabilities.models import Capability, CapabilityAction, CapabilityCategory
from ai.capabilities.registry import CapabilityRegistry, get_capability_registry


class TestCapabilityRegistry(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = get_capability_registry()

    def test_total_capabilities_registered(self) -> None:
        """Verify that at least 45+ total capabilities are registered."""
        self.assertGreaterEqual(self.registry.total_count, 45)

    def test_developer_clis_registered(self) -> None:
        """Verify all 8 local developer coding CLIs are registered."""
        expected_clis = ["antigravity", "claude", "codex", "copilot", "hermes", "aider", "opencode", "cline"]
        for cli in expected_clis:
            cap = self.registry.get_capability(f"developer-cli:{cli}")
            self.assertIsNotNone(cap, f"CLI capability for '{cli}' should be registered")
            self.assertTrue(cap.is_cli)
            self.assertEqual(cap.category, CapabilityCategory.DEVELOPER_TOOLS)
            self.assertIn("prompt", [p.name for a in cap.actions for p in a.parameters])

    def test_core_apps_registered(self) -> None:
        """Verify canonical core applications are present."""
        core_ids = [
            "youtube-summarizer",
            "document-qa",
            "research-assistant",
            "face-recognition",
            "system-telemetry",
            "desktop-pc-tools",
        ]
        for cid in core_ids:
            cap = self.registry.get_capability(cid)
            self.assertIsNotNone(cap, f"Core capability '{cid}' should be registered")
            self.assertTrue(len(cap.actions) >= 1)

    def test_extension_modules_registered(self) -> None:
        """Verify feature suite extension modules #1 to #43 are registered."""
        modules = [c for c in self.registry.list_capabilities() if c.id.startswith("module:")]
        self.assertGreaterEqual(len(modules), 40)
        
        # Test specific key modules
        m18 = self.registry.get_capability("module:18:multi_agent_orchestrator")
        self.assertIsNotNone(m18)
        self.assertEqual(m18.metadata.get("module_number"), 18)

        m24 = self.registry.get_capability("module:24:email_calendar_assistant")
        self.assertIsNotNone(m24)

        m33 = self.registry.get_capability("module:33:defensive_cybersecurity_agent")
        self.assertIsNotNone(m33)
        self.assertEqual(m33.minimum_role, "ADMIN")

    def test_filter_by_category(self) -> None:
        """Verify filtering capabilities by category."""
        dev_caps = self.registry.list_capabilities(category=CapabilityCategory.DEVELOPER_TOOLS)
        self.assertGreater(len(dev_caps), 0)
        for c in dev_caps:
            self.assertEqual(c.category, CapabilityCategory.DEVELOPER_TOOLS)

    def test_dynamic_registration(self) -> None:
        """Verify dynamic capability registration and unregistration for future plugins."""
        dyn_cap = Capability(
            id="plugin:custom-translator",
            name="Custom Japanese Neural Translator",
            category=CapabilityCategory.EDUCATION_LEARNING,
            tier="lightweight",
            description="Custom plugin translation engine.",
            is_plugin=True,
            is_builtin=False,
            keywords=["japanese", "translate japanese"],
            actions=[CapabilityAction(action_id="translate", name="Translate Text")],
        )
        self.registry.register_capability(dyn_cap)
        fetched = self.registry.get_capability("plugin:custom-translator")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "Custom Japanese Neural Translator")

        # Unregister
        ok = self.registry.unregister_capability("plugin:custom-translator")
        self.assertTrue(ok)
        self.assertIsNone(self.registry.get_capability("plugin:custom-translator"))


if __name__ == "__main__":
    unittest.main()
