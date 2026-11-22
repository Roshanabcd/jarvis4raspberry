"""Integration tests: manifest contract, persisted E-STOP across restarts, and replay flow."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.app.config import ComputerAssistantConfig
from backend.services.assistant_engine import ComputerAssistantEngine

ROOT = Path(__file__).resolve().parents[2]


class TestModule19Integration(unittest.TestCase):
    def test_manifest_contract_fields(self) -> None:
        m = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        for k in ("module_id", "module_number", "version", "contract_version", "permissions", "entrypoints", "events"):
            self.assertIn(k, m)
        self.assertEqual(m["module_number"], 19)

    def test_estop_persists_across_engine_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = ComputerAssistantConfig(db_path=str(Path(tmp) / "p.db"), sandbox_dir=str(Path(tmp) / "sb"))
            e1 = ComputerAssistantEngine(config=cfg)
            e1.engage_estop("Persisted stop", triggered_by="roshan")
            e1.db.close()

            e2 = ComputerAssistantEngine(config=cfg)
            self.assertTrue(e2.estop_active)
            self.assertEqual(e2.estop_reason, "Persisted stop")
            e2.db.close()


if __name__ == "__main__":
    unittest.main()
