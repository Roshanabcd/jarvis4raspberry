"""End-to-end tests for JARVIS Deep Learning Recommendation Engine."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from jarvis_recommendation_engine.app import create_app
from jarvis_recommendation_engine.config import RecommendationConfig


class TestRecommendationEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self._tmpdir.name) / "test_recs.db"
        cfg = RecommendationConfig(db_path=db_path)
        self.client = TestClient(create_app(config=cfg))

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _seed_catalog(self) -> None:
        items = [
            {
                "item_id": "ros2-nav",
                "title": "ROS2 Autonomous Navigation on Raspberry Pi 5",
                "category": "robotics",
                "description": "Configure Nav2 stack, LiDAR SLAM mapping, and obstacle avoidance on Raspberry Pi 5.",
                "tags": ["ros2", "robotics", "lidar", "raspberry-pi"],
            },
            {
                "item_id": "ros2-arm",
                "title": "Robotic Arm Inverse Kinematics with ROS2",
                "category": "robotics",
                "description": "Control servo joints, MoveIt2 trajectories, and LiDAR perception on Raspberry Pi 5.",
                "tags": ["ros2", "robotics", "kinematics", "raspberry-pi"],
            },
            {
                "item_id": "fastapi-wal",
                "title": "FastAPI Async SQLite WAL Architecture",
                "category": "backend",
                "description": "Build low-latency Python REST APIs with FastAPI, Pydantic, and SQLite WAL persistence.",
                "tags": ["fastapi", "python", "sqlite"],
            },
            {
                "item_id": "garden-herbs",
                "title": "Indoor Balcony Herb Gardening Guide",
                "category": "lifestyle",
                "description": "Grow basil, mint, and coriander in small terracotta pots with daily sunlight.",
                "tags": ["gardening", "plants", "home"],
            },
        ]
        for item in items:
            resp = self.client.post("/api/recommendations/items", json=item)
            self.assertEqual(resp.status_code, 200)

    def test_health_and_ui(self) -> None:
        ui = self.client.get("/recommendations")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("Deep Learning Recommendation Engine", ui.text)

        health = self.client.get("/api/recommendations/health")
        self.assertEqual(health.status_code, 200)
        body = health.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["embedding_dim"], 128)
        self.assertEqual(body["total_items"], 0)

    def test_hybrid_recommendations_and_similarity(self) -> None:
        self._seed_catalog()

        # Peer user likes both ROS2 robotics items (creates collaborative signal)
        self.assertEqual(
            self.client.post(
                "/api/recommendations/interactions",
                json={"user_id": "peer_eng", "item_id": "ros2-nav", "event_type": "complete"},
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                "/api/recommendations/interactions",
                json={"user_id": "peer_eng", "item_id": "ros2-arm", "event_type": "complete"},
            ).status_code,
            200,
        )

        # Target user completes ros2-nav; ros2-arm should rank #1 over unrelated gardening
        self.assertEqual(
            self.client.post(
                "/api/recommendations/interactions",
                json={"user_id": "roshan", "item_id": "ros2-nav", "event_type": "complete"},
            ).status_code,
            200,
        )

        rec_resp = self.client.post(
            "/api/recommendations/recommend",
            json={"user_id": "roshan", "top_k": 3, "exclude_interacted": True},
        )
        self.assertEqual(rec_resp.status_code, 200)
        rec_data = rec_resp.json()
        self.assertEqual(rec_data["strategy"], "hybrid_neural_collaborative")
        self.assertEqual(rec_data["recommendations"][0]["item_id"], "ros2-arm")
        self.assertGreater(
            rec_data["recommendations"][0]["final_score"],
            rec_data["recommendations"][-1]["final_score"],
        )

        # Item-to-item cosine similarity check
        sim_resp = self.client.get("/api/recommendations/items/ros2-nav/similar?top_k=3")
        self.assertEqual(sim_resp.status_code, 200)
        sim_data = sim_resp.json()
        self.assertEqual(sim_data["similar"][0]["item_id"], "ros2-arm")

    def test_cold_start_and_missing_item_handling(self) -> None:
        self._seed_catalog()
        # Cold-start user gets popularity fallback
        cold = self.client.post(
            "/api/recommendations/recommend",
            json={"user_id": "new_guest", "top_k": 2},
        )
        self.assertEqual(cold.status_code, 200)
        self.assertEqual(cold.json()["strategy"], "cold_start_popularity")
        self.assertEqual(len(cold.json()["recommendations"]), 2)

        # Interaction on missing item returns 404
        missing = self.client.post(
            "/api/recommendations/interactions",
            json={"user_id": "roshan", "item_id": "does-not-exist", "event_type": "like"},
        )
        self.assertEqual(missing.status_code, 404)


if __name__ == "__main__":
    unittest.main()
