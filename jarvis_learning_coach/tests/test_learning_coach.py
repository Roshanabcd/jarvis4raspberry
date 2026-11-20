"""End-to-end tests for JARVIS Personalized Learning AI Coach."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from jarvis_learning_coach.app import create_app
from jarvis_learning_coach.config import LearningCoachConfig


class TestLearningCoach(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self._tmpdir.name) / "test_coach.db"
        cfg = LearningCoachConfig(db_path=db_path)
        self.client = TestClient(create_app(config=cfg))

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_health_and_ui(self) -> None:
        ui = self.client.get("/learning-coach")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("Personalized Learning AI Coach", ui.text)

        health = self.client.get("/api/learning-coach/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["total_sessions"], 0)

    def test_socratic_session_hint_and_mastery_progression(self) -> None:
        sess = self.client.post(
            "/api/learning-coach/sessions",
            json={"learner_id": "roshan", "subject": "Backend", "concept": "FastAPI"},
        )
        self.assertEqual(sess.status_code, 200)
        s_data = sess.json()
        sid = s_data["session_id"]
        initial_mastery = s_data["mastery_score"]

        # Learner asks for a hint -> progressive scaffold
        hint_turn = self.client.post(
            f"/api/learning-coach/sessions/{sid}/respond",
            json={"message": "I am not sure where to start", "request_hint": True},
        )
        self.assertEqual(hint_turn.status_code, 200)
        self.assertEqual(hint_turn.json()["understanding_signal"], "needs_scaffold")
        self.assertEqual(hint_turn.json()["hint_level"], 1)

        # Learner provides strong explanation -> mastery increases
        good_turn = self.client.post(
            f"/api/learning-coach/sessions/{sid}/respond",
            json={
                "message": (
                    "FastAPI uses async endpoint handlers with Pydantic validation and modular router "
                    "dependency injection for clean APIs."
                )
            },
        )
        self.assertEqual(good_turn.status_code, 200)
        self.assertEqual(good_turn.json()["understanding_signal"], "strong_comprehension")
        self.assertGreater(good_turn.json()["mastery_score"], initial_mastery)

    def test_adaptive_exercise_grading_and_diagnostics(self) -> None:
        gen = self.client.post(
            "/api/learning-coach/exercises/generate",
            json={"learner_id": "roshan", "subject": "Databases", "concept": "SQLite WAL"},
        )
        self.assertEqual(gen.status_code, 200)
        ex_id = gen.json()["exercise_id"]

        sub = self.client.post(
            f"/api/learning-coach/exercises/{ex_id}/submit",
            json={
                "answer": (
                    "SQLite WAL mode improves concurrency by appending transaction writes to a write-ahead log "
                    "so readers do not lock writers, while foreign key constraints and indexes keep queries fast."
                )
            },
        )
        self.assertEqual(sub.status_code, 200)
        ev = sub.json()
        self.assertTrue(ev["passed"])
        self.assertGreaterEqual(ev["score"], 70.0)
        self.assertGreater(ev["updated_mastery"], 35.0)

        diag = self.client.get("/api/learning-coach/mastery/roshan")
        self.assertEqual(diag.status_code, 200)
        self.assertGreaterEqual(len(diag.json()["concepts"]), 1)
        self.assertIsNotNone(diag.json()["recommended_next_concept"])


if __name__ == "__main__":
    unittest.main()
