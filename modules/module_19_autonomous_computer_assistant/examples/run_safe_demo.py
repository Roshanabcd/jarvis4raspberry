"""Standalone safe-demo CLI exercising screenshot, approval gate, sandbox file write, and replay."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.module_19_autonomous_computer_assistant.backend.app.config import ComputerAssistantConfig
from modules.module_19_autonomous_computer_assistant.backend.services.assistant_engine import ComputerAssistantEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cfg = ComputerAssistantConfig(db_path=str(Path(tmp) / "demo.db"), sandbox_dir=str(Path(tmp) / "sandbox"))
        eng = ComputerAssistantEngine(config=cfg)
        try:
            a1 = eng.submit_action("capture_screenshot", {})
            a2 = eng.submit_action("file_write", {"path": "demo_note.txt", "content": "Safe sandboxed write!"})
            apr_id = a2["approval"]["approval_id"]
            dec = eng.decide_approval(apr_id, approved=True, decided_by="demo-cli")
            rep = eng.replay_actions([a1["action_id"]], dry_run=True)
            print(json.dumps({"screenshot_action": a1["status"], "approved_write": dec["action"]["status"], "dry_replay_count": rep["replayed_count"]}, indent=2))
        finally:
            eng.db.close()


if __name__ == "__main__":
    main()
