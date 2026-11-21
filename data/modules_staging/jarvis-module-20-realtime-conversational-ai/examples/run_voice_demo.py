"""Runnable CLI demo for Module 20: ARIA & ATLAS turns + visemes + error recovery."""

from __future__ import annotations

import asyncio, json, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import ConversationalConfig
from backend.services.conversation_engine import ConversationalEngine


async def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        eng = ConversationalEngine(ConversationalConfig(db_path=str(Path(tmp) / "demo.db")))
        try:
            r1 = await eng.complete_turn(None, "Hello ARIA, status check!", persona="aria")
            r2 = await eng.complete_turn(r1["session_id"], "Test fallback", persona="atlas", simulate_provider_error=True)
            print(json.dumps({
                "aria_reply": r1["assistant_message"]["content"],
                "viseme_count": len(r1["visemes"]),
                "lip_sync_mode": r1["lip_sync_mode"],
                "atlas_fallback_used": r2["fallback_used"],
            }, indent=2))
        finally:
            eng.db.close()


if __name__ == "__main__":
    asyncio.run(main())
