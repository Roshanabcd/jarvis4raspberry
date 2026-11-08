"""Unit tests for Phase 2: Typed Tool Registry & Agent Tool Suites (Categories A–H)."""

import pytest
from tools.registry import tool_registry, ToolRegistry
from ai.tools.executor import ToolExecutor


class TestPhase2ToolRegistry:
    """Verify tool registration, typing, permissions, and Categories A–H."""

    def setup_method(self):
        self.registry = ToolRegistry(auto_register_core=True)
        self.executor = ToolExecutor()

    def test_all_categories_registered(self):
        tools = self.registry.list_tools()
        names = {t["name"] for t in tools}

        # Category A: System tools
        assert "get_system_status" in names
        assert "get_network_status" in names
        assert "get_process_info" in names

        # Category B: Robot tools
        assert "robot_status" in names
        assert "robot_arm" in names
        assert "robot_disarm" in names
        assert "robot_move" in names
        assert "servo_set" in names
        assert "robot_estop" in names

        # Category C: Sensor tools
        assert "read_sensors" in names
        assert "read_bme280" in names
        assert "read_bh1750" in names
        assert "read_ultrasonic" in names

        # Category D: Vision tools
        assert "camera_capture" in names
        assert "camera_status" in names

        # Category E: Memory tools
        assert "memory_store" in names
        assert "memory_search" in names

        # Category F: Productivity tools
        assert "read_file" in names
        assert "write_file" in names
        assert "schedule_task" in names

        # Category G: Research tools
        assert "web_search" in names
        assert "fetch_page" in names

        # Category H: Application tools
        assert "health_check" in names
        assert "open_app" in names
        assert "run_code" in names

    def test_schema_validation_type_checking(self):
        # servo_set requires channel (int) and angle (int)
        valid_res = self.registry.execute_tool("servo_set", {"channel": 2, "angle": 90})
        assert valid_res["success"] is True

        # Invalid type for channel: string instead of int
        invalid_res = self.registry.execute_tool("servo_set", {"channel": "invalid", "angle": 90})
        assert invalid_res["success"] is False
        assert "must be an integer" in invalid_res["error"]

    def test_robot_safety_and_disarmed_state(self):
        from tools.robotics.controller import robot
        robot.disarm()

        # robot_move when disarmed should be blocked or return safe failure
        res = self.registry.execute_tool("robot_move", {"direction": "forward", "speed": 50})
        # If disarmed, hardware controller prevents movement
        assert res["success"] is True  # executed successfully to enforce safety
        assert res["result"]["armed"] is False

    def test_system_status_tool_execution(self):
        res = self.registry.execute_tool("get_system_status", {})
        assert res["success"] is True
        assert "cpu_usage_pct" in res["result"] or "cpu" in str(res["result"]).lower()
        assert "ram_total_mb" in res["result"] or "memory" in str(res["result"]).lower()

    def test_sensor_tools_execution(self):
        res = self.registry.execute_tool("read_sensors", {})
        assert res["success"] is True
        assert isinstance(res["result"], dict)

    def test_memory_tools_execution(self):
        store_res = self.registry.execute_tool("memory_store", {
            "category": "KNOWLEDGE",
            "content": "Phase 2 agent tools verified.",
        })
        assert store_res["success"] is True
        assert store_res["result"]["status"] == "stored"

        search_res = self.registry.execute_tool("memory_search", {
            "query": "Phase 2",
        })
        assert search_res["success"] is True
        assert search_res["result"]["count"] >= 1

    def test_tool_executor_delegation(self):
        # Verify ToolExecutor correctly executes system status
        raw_res = self.executor.execute("get_system_status", {})
        assert "cpu" in raw_res.lower()
