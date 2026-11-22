"""End-to-end tests for JARVIS Smart Resume Matching."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from jarvis_resume_matching.app import create_app
from jarvis_resume_matching.config import ResumeMatchingConfig


class TestResumeMatching(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self._tmpdir.name) / "test_resume.db"
        cfg = ResumeMatchingConfig(db_path=db_path)
        self.client = TestClient(create_app(config=cfg))

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_health_and_ui(self) -> None:
        ui = self.client.get("/resume-matching")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("Smart Resume Matching", ui.text)

        health = self.client.get("/api/resume-matching/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["total_jobs"], 0)

    def test_job_creation_candidate_ranking_and_gap_analysis(self) -> None:
        job_resp = self.client.post(
            "/api/resume-matching/jobs",
            json={
                "title": "Robotics & AI Backend Engineer",
                "company": "JARVIS Robotics",
                "description": (
                    "Seeking an engineer with 3+ years of experience building Python, FastAPI, SQLite, "
                    "ROS2, and Raspberry Pi 5 autonomous robotics backends with Docker."
                ),
                "required_skills": ["python", "fastapi", "sqlite", "ros 2", "rpi5"],
                "preferred_skills": ["docker", "opencv"],
                "min_years_experience": 3.0,
            },
        )
        self.assertEqual(job_resp.status_code, 200)
        job_id = job_resp.json()["job_id"]
        self.assertIn("ros2", job_resp.json()["required_skills"])
        self.assertIn("raspberry pi", job_resp.json()["required_skills"])

        # Strong candidate
        strong = self.client.post(
            "/api/resume-matching/match",
            json={
                "job_id": job_id,
                "candidate_name": "Aarav Tech",
                "resume_text": (
                    "B.Tech Computer Engineering with 4 years of experience in Python, FastAPI, SQLite WAL, "
                    "ROS2 robotics navigation on Raspberry Pi 5, Docker containers, and OpenCV vision."
                ),
            },
        )
        self.assertEqual(strong.status_code, 200)
        s_data = strong.json()
        self.assertEqual(s_data["recommendation_tier"], "strong_match")
        self.assertEqual(len(s_data["missing_required_skills"]), 0)
        self.assertEqual(s_data["candidate_education"], "Bachelor's Degree")

        # Partial candidate with clear skill gaps
        weak = self.client.post(
            "/api/resume-matching/match",
            json={
                "job_id": job_id,
                "candidate_name": "Bikash Web",
                "resume_text": (
                    "Frontend developer with 1 year of experience in HTML, CSS, JavaScript, and React "
                    "building marketing landing pages."
                ),
            },
        )
        self.assertEqual(weak.status_code, 200)
        w_data = weak.json()
        self.assertLess(w_data["overall_score"], s_data["overall_score"])
        self.assertIn("fastapi", w_data["missing_required_skills"])
        self.assertGreaterEqual(len(w_data["gap_recommendations"]), 1)

        # Leaderboard ranks strong candidate #1
        lb = self.client.get(f"/api/resume-matching/jobs/{job_id}/leaderboard")
        self.assertEqual(lb.status_code, 200)
        self.assertEqual(lb.json()["total_candidates"], 2)
        self.assertEqual(lb.json()["candidates"][0]["candidate_name"], "Aarav Tech")


if __name__ == "__main__":
    unittest.main()
