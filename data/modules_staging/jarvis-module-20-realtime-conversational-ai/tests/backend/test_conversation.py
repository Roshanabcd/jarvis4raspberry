"""Backend unit & async tests for ConversationalEngine (Module 20)."""

from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from backend.app.config import ConversationalConfig
from backend.services.conversation_engine import ConversationalEngine, generate_approximate_visemes


class TestConversationalEngine(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.eng = ConversationalEngine(ConversationalConfig(db_path=str(Path(self._tmp.name) / "m20.db")))

    async def asyncTearDown(self) -> None:
        self.eng.db.close()
        self._tmp.cleanup()

    async def test_aria_and_atlas_turns_with_visemes_and_history(self) -> None:
        r1 = await self.eng.complete_turn(None, "Hello JARVIS", persona="aria")
        self.assertEqual(r1["lip_sync_mode"], "approximate_syllable_viseme")
        self.assertGreater(len(r1["visemes"]), 3)
        self.assertIn("ARIA", r1["assistant_message"]["content"])

        sid = r1["session_id"]
        r2 = await self.eng.complete_turn(sid, "Status check", persona="atlas")
        self.assertIn("ATLAS", r2["assistant_message"]["content"])

        msgs = self.eng.db.list_messages(sid)
        self.assertEqual(len(msgs), 4)

    async def test_provider_error_recovery_fallback(self) -> None:
        res = await self.eng.complete_turn(None, "Test recovery", persona="aria", simulate_provider_error=True)
        self.assertTrue(res["fallback_used"])
        self.assertIn("Simulated primary AI provider outage", res["recovery_error"])
        self.assertTrue(res["assistant_message"]["fallback_used"])

    async def test_mid_stream_barge_in_interruption(self) -> None:
        session = self.eng.create_session("Interrupt Test", persona="aria")
        sid = session["session_id"]
        events = []
        async for evt in self.eng.stream_turn(sid, "Give me a detailed status response please", persona="aria"):
            events.append(evt)
            if evt["event"] == "turn.token" and len(events) >= 3:
                self.eng.interrupt_session(sid)
        self.assertEqual(events[-1]["event"], "turn.interrupted")
        self.assertTrue(events[-1]["assistant_message"]["interrupted"])

    def test_viseme_generator_ends_at_rest(self) -> None:
        cues = generate_approximate_visemes("Hello ARIA")
        self.assertEqual(cues[-1]["viseme"], "REST")
        self.assertLess(cues[-1]["openness"], 0.1)


if __name__ == "__main__":
    unittest.main()
