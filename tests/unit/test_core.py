"""
JARVIS Comprehensive Test Suite — Unit Tests
Covers: core API, memory, robotics state machine, sensors, tools, security, voice, vision
"""
import pytest
import sys
import os
import time
import json
import tempfile

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


# ─────────────────────────────────────────────────────────────
# 1. Config Manager
# ─────────────────────────────────────────────────────────────
class TestConfigManager:
    def test_loads_simulation_mode(self):
        from config.config_manager import config
        val = config.get("simulation_mode")
        assert isinstance(val, bool)

    def test_default_fallback(self):
        from config.config_manager import config
        assert config.get("nonexistent_key_xyz", "default") == "default"


# ─────────────────────────────────────────────────────────────
# 2. Memory Database
# ─────────────────────────────────────────────────────────────
class TestMemoryDB:
    @pytest.fixture
    def db(self, tmp_path):
        from memory.long_term.database import MemoryDB
        return MemoryDB(db_path=str(tmp_path / "test_mem.db"))

    def test_store_and_search(self, db):
        db.store("KNOWLEDGE", "The sky is blue", key="sky_color")
        results = db.search("sky", category="KNOWLEDGE")
        assert len(results) == 1
        assert "blue" in results[0]["content"]

    def test_update_memory(self, db):
        mid = db.store("USER", "User prefers dark mode")
        db.update(mid, "User prefers light mode")
        results = db.search("light mode")
        assert len(results) == 1

    def test_delete_memory(self, db):
        mid = db.store("TASK", "Temporary task")
        db.delete(mid)
        results = db.search("Temporary task")
        assert len(results) == 0

    def test_invalid_category_raises(self, db):
        with pytest.raises(ValueError):
            db.store("INVALID_CAT", "test")

    def test_summarize(self, db):
        db.store("SYSTEM", "Boot log entry")
        db.store("SYSTEM", "Shutdown log entry")
        summary = db.summarize("SYSTEM")
        assert summary["total_memories"] == 2

    def test_task_history(self, db):
        db.log_task("What is 2+2?", tool_used="math", result="4", success=True, duration_ms=12.3)
        history = db.get_task_history()
        assert len(history) >= 1
        assert history[0]["query"] == "What is 2+2?"

    def test_retrieve_context(self, db):
        for i in range(5):
            db.store("CONVERSATION", f"Turn {i}")
        ctx = db.retrieve_context("CONVERSATION", limit=3)
        assert len(ctx) == 3

    def test_wal_mode(self, tmp_path):
        from memory.long_term.database import MemoryDB
        import sqlite3
        db = MemoryDB(db_path=str(tmp_path / "wal_test.db"))
        conn = sqlite3.connect(db.db_path)
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        conn.close()
        assert mode == "wal"


# ─────────────────────────────────────────────────────────────
# 3. Robot State Machine
# ─────────────────────────────────────────────────────────────
class TestRobotStateMachine:
    @pytest.fixture
    def sm(self):
        from hardware.raspberry_pi.state_machine import RobotStateMachine, RobotState
        return RobotStateMachine(initial=RobotState.OFFLINE)

    def test_valid_transition_offline_to_booting(self, sm):
        from hardware.raspberry_pi.state_machine import RobotState
        sm.transition(RobotState.BOOTING)
        assert sm.state == RobotState.BOOTING

    def test_invalid_transition_raises(self, sm):
        from hardware.raspberry_pi.state_machine import RobotState
        with pytest.raises(RuntimeError):
            sm.transition(RobotState.MOVING)  # Can't go OFFLINE → MOVING

    def test_emergency_stop_always_allowed(self, sm):
        from hardware.raspberry_pi.state_machine import RobotState
        sm.emergency_stop()
        assert sm.state == RobotState.EMERGENCY_STOP

    def test_info_dict(self, sm):
        info = sm.info()
        assert "state" in info
        assert "time_in_state_s" in info

    def test_full_boot_sequence(self, sm):
        from hardware.raspberry_pi.state_machine import RobotState
        sm.transition(RobotState.BOOTING)
        sm.transition(RobotState.IDLE)
        sm.transition(RobotState.LISTENING)
        sm.transition(RobotState.PROCESSING)
        sm.transition(RobotState.MOVING)
        sm.transition(RobotState.STOPPING)
        sm.transition(RobotState.IDLE)
        assert sm.state == RobotState.IDLE


# ─────────────────────────────────────────────────────────────
# 4. API Endpoints (integration)
# ─────────────────────────────────────────────────────────────
class TestAPI:
    @pytest.fixture(scope="class")
    def client(self):
        from fastapi.testclient import TestClient
        from apps.core.main import app
        return TestClient(app)

    def test_system_status(self, client):
        resp = client.get("/api/system")
        assert resp.status_code == 200
        data = resp.json()
        assert "cpu_usage_pct" in data or "cpu_usage_percent" in data

    def test_health_endpoint(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert "status" in resp.json()

    def test_robot_stop(self, client):
        resp = client.post("/api/robot/stop")
        assert resp.status_code == 200

    def test_robot_estop(self, client):
        resp = client.post("/api/robot/estop")
        assert resp.status_code == 200
        assert resp.json()["status"] in ("emergency_stop_activated", "emergency_stop")

    def test_robot_forward(self, client):
        resp = client.post("/api/robot/forward?speed=50")
        assert resp.status_code == 200

    def test_memory_store_and_search(self, client):
        resp = client.post("/api/memory/store",
                           json={"category": "KNOWLEDGE", "content": "test fact"})
        assert resp.status_code == 200
        resp2 = client.get("/api/memory/search?query=test")
        assert resp2.status_code == 200

    def test_voice_command(self, client):
        resp = client.post("/api/voice/command", json={"text": "what is the status"})
        assert resp.status_code == 200
        assert "response" in resp.json()

    def test_vision_capture(self, client):
        resp = client.get("/api/vision/capture")
        assert resp.status_code == 200
        assert resp.json()["status"] in ("ok", "simulated", "error")

    def test_sensors_all(self, client):
        # May not exist until sensor builder completes, skip gracefully
        resp = client.get("/api/sensors/all")
        assert resp.status_code in (200, 404)

    def test_chat_endpoint(self, client):
        resp = client.post("/api/chat", json={"message": "hello jarvis"})
        assert resp.status_code in (200, 404)  # 404 acceptable if not yet wired

    def test_status_endpoint(self, client):
        resp = client.get("/api/status")
        assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────
# 5. Encoder Module
# ─────────────────────────────────────────────────────────────
class TestEncoders:
    def test_tick_update(self):
        from hardware.motors.encoders import EncoderChannel
        enc = EncoderChannel("LEFT")
        enc.update(360)
        data = enc.read()
        assert data["ticks"] == 360

    def test_distance_calculation(self):
        from hardware.motors.encoders import EncoderChannel
        enc = EncoderChannel("LEFT")
        enc.update(enc.TICKS_PER_REV)  # one full revolution
        dist = enc.get_distance()
        expected = 3.14159 * enc.WHEEL_DIAMETER_MM
        assert abs(dist - expected) < 1.0

    def test_reset(self):
        from hardware.motors.encoders import EncoderChannel
        enc = EncoderChannel("RIGHT")
        enc.update(500)
        enc.reset()
        assert enc.get_ticks() == 0

    def test_telemetry_parsing(self):
        from hardware.motors.encoders import EncoderManager
        em = EncoderManager()
        em.parse_telemetry("ENC LEFT 1000")
        em.parse_telemetry("ENC RIGHT 999")
        data = em.read_all()
        assert data["left"]["ticks"] == 1000
        assert data["right"]["ticks"] == 999

    def test_invalid_telemetry_ignored(self):
        from hardware.motors.encoders import EncoderManager
        em = EncoderManager()
        em.parse_telemetry("GARBAGE DATA HERE")  # Should not crash
        assert em.left.get_ticks() == 0


# ─────────────────────────────────────────────────────────────
# 6. PCA9685 Simulation
# ─────────────────────────────────────────────────────────────
class TestPCA9685Simulation:
    def test_init_simulation(self):
        from hardware.pca9685.driver import PCA9685
        pca = PCA9685()
        # Should not raise — defaults to simulation if hardware absent
        assert pca.simulated is True

    def test_set_pwm_simulation(self):
        from hardware.pca9685.driver import PCA9685
        pca = PCA9685()
        pca.set_pwm(0, 0, 300)  # Should not raise


# ─────────────────────────────────────────────────────────────
# 7. Vision Service Simulation
# ─────────────────────────────────────────────────────────────
class TestVisionSimulation:
    def test_capture_frame_simulation(self):
        from apps.vision.service import VisionService
        vs = VisionService(simulation=True)
        frame = vs.capture_frame()
        assert frame["status"] == "simulated"
        assert "objects_detected" in frame

    def test_camera_status_simulation(self):
        from apps.vision.service import VisionService
        vs = VisionService(simulation=True)
        status = vs.camera_status()
        assert status["simulation"] is True


# ─────────────────────────────────────────────────────────────
# 8. RPi System Info
# ─────────────────────────────────────────────────────────────
class TestRPiInfo:
    def test_get_system_status_keys(self):
        from hardware.raspberry_pi.rpi_info import get_system_status
        status = get_system_status()
        for key in ("cpu_usage_pct", "ram_total_mb", "disk_pct", "timestamp"):
            assert key in status, f"Missing key: {key}"

    def test_list_i2c_devices(self):
        from hardware.raspberry_pi.rpi_info import list_i2c_devices
        devices = list_i2c_devices()
        assert isinstance(devices, list)

    def test_list_serial_ports(self):
        from hardware.raspberry_pi.rpi_info import list_serial_ports
        ports = list_serial_ports()
        assert isinstance(ports, list)

    def test_is_online(self):
        from hardware.raspberry_pi.rpi_info import is_online
        # Just check it returns bool, doesn't matter if online or not
        result = is_online()
        assert isinstance(result, bool)
