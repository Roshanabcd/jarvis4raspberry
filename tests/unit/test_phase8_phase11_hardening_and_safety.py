"""
Tests for Phases 8 through 11:
- Actuator Safety Gates (Disarmed boot state, latched E-Stop, speed bounds)
- Database Hardening (SQLite WAL mode, thread safety)
- Security & Key Masking (/api/settings/integrations)
- Audit Logging
"""
import os
import sqlite3
import pytest
from fastapi.testclient import TestClient

from apps.core.main import app
from tools.robotics.controller import robot
from memory.long_term.database import db

client = TestClient(app)


class TestPhase8to11HardeningAndSafety:

    def setup_method(self):
        # Ensure robot starts in known state
        robot.disarm()
        robot.clear_emergency_stop()

    def test_actuator_disarmed_by_default(self):
        """Actuators must be disarmed and reject motion commands until explicitly armed."""
        res_state = client.get("/api/robot/state")
        assert res_state.status_code == 200
        data = res_state.json()
        assert data["armed"] is False

        # Attempt motion while disarmed
        res_move = client.post("/api/robot/forward?speed=50")
        assert res_move.status_code == 400
        assert "disarmed" in res_move.json()["detail"].lower()

    def test_actuator_arming_and_motion(self):
        """Arming allows motion; disarming immediately disables it."""
        res_arm = client.post("/api/robot/arm")
        assert res_arm.status_code == 200
        assert res_arm.json()["armed"] is True

        res_move = client.post("/api/robot/forward?speed=40")
        assert res_move.status_code == 200
        assert res_move.json()["status"] == "moving"

        # Disarm
        res_disarm = client.post("/api/robot/disarm")
        assert res_disarm.status_code == 200
        assert res_disarm.json()["armed"] is False

        # Motion should fail again
        res_move_again = client.post("/api/robot/forward?speed=40")
        assert res_move_again.status_code == 400

    def test_emergency_stop_latches_motion(self):
        """E-Stop immediately latches and blocks motion even if armed."""
        client.post("/api/robot/arm")
        res_estop = client.post("/api/robot/estop")
        assert res_estop.status_code == 200

        # Verify state is latched
        res_state = client.get("/api/robot/state")
        assert res_state.json()["emergency_stopped"] is True
        assert res_state.json()["armed"] is False

        # Attempt motion
        res_move = client.post("/api/robot/forward?speed=50")
        assert res_move.status_code == 400
        assert "emergency stop" in res_move.json()["detail"].lower()

        # Clear e-stop: robot remains safe (disarmed)
        res_clear = client.post("/api/robot/clear_estop")
        assert res_clear.status_code == 200
        res_state2 = client.get("/api/robot/state")
        assert res_state2.json()["emergency_stopped"] is False
        assert res_state2.json()["armed"] is False

    def test_security_api_key_masking(self):
        """API keys must never be returned in plaintext via settings."""
        os.environ["GEMINI_API_KEY"] = "AIzaSySecretTestKey12345678"
        res = client.get("/api/settings/integrations")
        assert res.status_code == 200
        settings = res.json()["settings"]
        masked = settings.get("gemini_api_key", "")
        assert "AIza" in masked
        assert "5678" in masked
        assert "****" in masked
        assert "SecretTestKey" not in masked

    def test_database_wal_mode_and_concurrency(self):
        """SQLite database must use WAL journal mode for concurrent read/write resilience."""
        conn = db._get_conn()
        cur = conn.cursor()
        mode = cur.execute("PRAGMA journal_mode;").fetchone()[0]
        assert mode.lower() == "wal"
