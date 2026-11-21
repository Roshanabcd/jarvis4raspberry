"""Integration tests: manifest contract & SQLite session persistence across restarts."""

from __future__ import annotations

import asyncio, json, tempfile, unittest
from pathlib import Path

from modules.module_20_realtime_conversational_ai.backend.app.config import ConversationalConfig
from modules.module_20_realtime_conversational_ai.backend.services.conversation_engine import ConversationalEngine

ROOT = Path(__file__).resolve().parents[2]


class TestModule20Integration(unittest.TestCase):
    def test_manifest_contract_fields(self) -> None:
        m = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(m["module_number"], 20)
        self.assertIn("lip_sync_accuracy", m["simulation_disclosure"])

    def test_conversation_history_persists_across_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "p20.db")
            e1 = ConversationalEngine(ConversationalConfig(db_path=db_path))
            res = asyncio.run(e1.complete_turn(None, "Remember this turn", persona="aria"))
            sid = res["session_id"]
            e1.db.close()

            e2 = ConversationalEngine(ConversationalConfig(db_path=db_path))
            msgs = e2.db.list_messages(sid)
            self.assertEqual(len(msgs), 2)
            self.assertEqual(msgs[0]["content"], "Remember this turn")
            e2.db.close()


if __name__ == "__main__":
    unittest.main()
