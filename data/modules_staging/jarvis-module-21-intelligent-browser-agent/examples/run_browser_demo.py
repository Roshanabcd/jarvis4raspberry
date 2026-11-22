"""Runnable CLI demonstration for JARVIS Module 21 — Intelligent Browser Agent."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import BrowserAgentConfig
from backend.services.browser_engine import BrowserAgentError, IntelligentBrowserEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cfg = BrowserAgentConfig(
            db_path=str(Path(tmp) / "demo_browser_agent.db"),
            downloads_dir=str(Path(tmp) / "downloads"),
        )
        engine = IntelligentBrowserEngine(cfg)

        print("1. Creating browser session (simulated local fixture)...")
        session = engine.create_session("Demo Session", "https://docs.jarvis.local/overview")
        sid = session["session_id"]
        inspected = engine.inspect_page(sid)
        print(f"   Session ID: {sid} | Title: {inspected['dom']['title']}")

        print("2. Verifying SSRF block on http://127.0.0.1:8121/admin...")
        try:
            engine.navigate(sid, "http://127.0.0.1:8121/admin")
        except BrowserAgentError as exc:
            print(f"   Blocked as expected [{exc.code}]: {exc.message}")

        print("3. Capturing and analyzing Pillow screenshot...")
        shot = engine.screenshot_and_analyze(sid)
        print(f"   Screenshot: {shot['width']}x{shot['height']} | Analysis: {shot['analysis']}")

        print("4. Running multi-page workflow (docs -> feedback form -> download)...")
        wf = engine.run_workflow(
            "Operator Feedback & Release Download",
            [
                {"action": "navigate", "params": {"url": "https://portal.jarvis.local/feedback"}},
                {"action": "inspect", "params": {}},
                {
                    "action": "submit_form",
                    "params": {
                        "form_id": "feedback-form",
                        "fields": {"operator": "Roshan", "module": "module-21", "notes": "CLI Demo"},
                    },
                },
                {"action": "download", "params": {"url": "https://releases.jarvis.local/files/jarvis_release_notes.txt"}},
            ],
            session_id=sid,
        )
        approval_id = wf["results"][-1]["approval_id"]
        print(f"   Workflow paused at status: {wf['status']} | Pending approval: {approval_id}")

        print("5. Approving form submission to resume workflow...")
        decision = engine.decide_approval(approval_id, approved=True, decided_by="roshan", comment="Verified")
        print(f"   Approval status: {decision['approval']['status']}")
        print(f"   Resumed workflow status: {decision['workflow']['status']} | Steps completed: {decision['workflow']['current_step']}")

        downloads = engine.db.list_downloads()
        print(f"6. Sandboxed downloads recorded: {len(downloads)} (SHA-256: {downloads[0]['sha256'][:16]}...)")
        engine.db.close()
        print("Demo complete.")


if __name__ == "__main__":
    main()
