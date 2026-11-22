"""Runnable CLI demonstration for JARVIS Module 26 — Project Autopilot."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.module_26_project_autopilot.backend.app.config import ProjectAutopilotConfig
from modules.module_26_project_autopilot.backend.services.autopilot_engine import ProjectAutopilotEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cfg = ProjectAutopilotConfig(
            db_path=os.path.join(tmp, "demo_m26.db"),
            workspace_root=os.path.join(tmp, "workspaces"),
        )
        engine = ProjectAutopilotEngine(config=cfg)

        bundle = engine.create_project(
            {
                "name": "Pi5 Edge Telemetry Hub",
                "goal": "Collect CPU/thermal metrics on Raspberry Pi 5 and expose REST alerts.",
                "tech_stack": ["Python", "FastAPI", "SQLite"],
                "dry_run": True,
                "auto_plan": True,
            }
        )
        pid = bundle["project"]["project_id"]
        step1 = engine.advance_project(pid, max_steps=10)
        paused = step1["paused_for_approval"]
        print(f"Project Created : {pid} ({bundle['project']['name']})")
        print(f"Executed Before Gate : {step1['executed_count']} tasks ({step1['progress_pct']}%)")
        print(f"Paused At Gate       : {len(paused)} task(s)")

        if paused:
            engine.decide_approval(paused[0]["task_id"], decision="approve", reviewer="roshan", note="Ship it")
            step2 = engine.advance_project(pid, max_steps=5)
            print(f"Post-Approval Progress: {step2['progress_pct']}% ({step2['project']['status']})")

        scaf = engine.scaffold_workspace(pid, include_tests=True)
        print(f"Scaffolded Files     : {scaf['created_files']}")
        print("\n--- Blueprint Preview ---\n")
        print(engine.export_blueprint_markdown(pid))


if __name__ == "__main__":
    main()
