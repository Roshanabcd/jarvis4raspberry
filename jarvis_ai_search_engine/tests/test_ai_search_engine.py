"""End-to-end tests for JARVIS End-to-End AI Search Engine."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from jarvis_ai_search_engine.app import create_app
from jarvis_ai_search_engine.config import AISearchConfig


class TestAISearchEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        cfg = AISearchConfig(
            db_path=self.root / "search.db",
            allowed_roots=[self.root],
        )
        self.client = TestClient(create_app(config=cfg))

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_health_and_ui(self) -> None:
        ui = self.client.get("/ai-search")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("End-to-End AI Search Engine", ui.text)

        health = self.client.get("/api/ai-search/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["total_sources"], 0)

    def test_unified_multi_source_search_and_filtering(self) -> None:
        sources = [
            {
                "source_type": "codebase",
                "title": "voice_pipeline.py",
                "source_uri": "local://jarvis/voice_pipeline.py",
                "content": "def detect_silence(audio_frames, timeout_sec=3.0):\n    '''Detect 3s silence window on ReSpeaker mic.'''\n    return timeout_sec\n",
                "tags": ["voice", "audio"],
            },
            {
                "source_type": "terminal_log",
                "title": "jarvis_daemon.log",
                "source_uri": "local:///var/log/jarvis_daemon.log",
                "content": "2026-11-20 05:10:01 INFO Starting JARVIS OS\n2026-11-20 05:10:04 ERROR ReSpeaker USB microphone buffer underrun on channel 0\n",
                "tags": ["logs", "audio"],
            },
            {
                "source_type": "web_knowledge",
                "title": "SQLite WAL Performance Notes",
                "source_uri": "https://sqlite.org/wal.html",
                "content": "Write-Ahead Logging (WAL) allows concurrent readers alongside a single writer in SQLite databases.",
                "tags": ["sqlite", "database"],
            },
        ]
        for s in sources:
            resp = self.client.post("/api/ai-search/index", json=s)
            self.assertEqual(resp.status_code, 200)

        # Unified search across all sources
        q = self.client.post(
            "/api/ai-search/query",
            json={"query": "ReSpeaker microphone silence or buffer underrun", "top_k": 5},
        )
        self.assertEqual(q.status_code, 200)
        q_data = q.json()
        self.assertGreaterEqual(q_data["total_hits"], 2)
        self.assertIn("ReSpeaker", q_data["synthesized_answer"])

        # Filter strictly to terminal_log
        q_log = self.client.post(
            "/api/ai-search/query",
            json={"query": "ReSpeaker underrun", "source_types": ["terminal_log"], "top_k": 5},
        )
        self.assertEqual(q_log.status_code, 200)
        hits = q_log.json()["hits"]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["source_type"], "terminal_log")
        self.assertIn("ERROR", hits[0]["location"])

        # History recorded
        hist = self.client.get("/api/ai-search/history")
        self.assertEqual(hist.status_code, 200)
        self.assertGreaterEqual(hist.json()["total"], 2)

    def test_directory_indexing_and_root_guard(self) -> None:
        ws = self.root / "sample_repo"
        ws.mkdir()
        (ws / "motor.py").write_text("def emergency_stop():\n    return 'E-STOP ENGAGED'\n", encoding="utf-8")
        (ws / "notes.md").write_text("# Safety\nAlways engage E-STOP before servicing servos.\n", encoding="utf-8")

        res = self.client.post("/api/ai-search/index-directory", json={"directory": str(ws)})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["indexed_files"], 2)

        # Path outside allowed_roots must be rejected with 403
        blocked = self.client.post("/api/ai-search/index-directory", json={"directory": "/etc"})
        self.assertEqual(blocked.status_code, 403)


if __name__ == "__main__":
    unittest.main()
