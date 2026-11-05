"""
Actuator Safety Suite for JARVIS OS.
Validates:
- Actuators boot in DISARMED state.
- Motion commands are blocked when disarmed.
- Emergency stop locks out movement and disarms actuators.
- Emergency stop cannot be bypassed without explicit clear_emergency_stop().
- Speed limits and servo bounds validation.
"""

import pytest
from tools.robotics.controller import RobotController
from hardware.pca9685.driver import PCA9685
from hardware.tb6612.driver import TB6612Controller


class DummyComm:
    def __init__(self):
        self.sent_commands = []
    def send_command(self, cmd: str):
        self.sent_commands.append(cmd)


class TestActuatorSafety:
    def test_boot_in_disarmed_state(self):
        controller = RobotController()
        assert controller.armed is False
        assert controller.is_armed is False

    def test_motion_blocked_when_disarmed(self):
        controller = RobotController()
        assert controller.armed is False
        success = controller.forward(50)
        assert success is False
        assert controller.state != "MOVING_FORWARD"

        success_rev = controller.backward(50)
        assert success_rev is False

        success_left = controller.turn_left(40)
        assert success_left is False

        success_right = controller.turn_right(40)
        assert success_right is False

    def test_motion_allowed_after_explicit_arm(self):
        controller = RobotController()
        arm_res = controller.arm()
        assert arm_res["status"] == "ok"
        assert controller.is_armed is True

        success = controller.forward(40)
        assert success is True
        assert controller.state == "MOVING_FORWARD"

    def test_emergency_stop_lockout(self):
        controller = RobotController()
        controller.arm()
        controller.forward(50)

        # Trigger e-stop
        controller.emergency_stop()
        assert controller.state == "EMERGENCY_STOP"
        assert controller.is_emergency_stopped is True
        assert controller.armed is False

        # Attempting motion while e-stop is active must fail
        assert controller.forward(30) is False
        assert controller.backward(30) is False
        assert controller.state == "EMERGENCY_STOP"

        # Attempting to arm while e-stop is active must fail
        arm_res = controller.arm()
        assert arm_res["status"] == "error"
        assert controller.armed is False

        # Must explicitly clear e-stop
        clear_res = controller.clear_emergency_stop()
        assert clear_res["status"] == "ok"
        assert controller.is_emergency_stopped is False
        # Still disarmed after clearing e-stop for safety!
        assert controller.armed is False

        # Re-arm required
        controller.arm()
        assert controller.forward(30) is True

    def test_speed_clamping(self):
        controller = RobotController()
        controller.arm()
        # Requesting speed 999 should be clamped to max_speed (100)
        valid, safe_speed, err = controller._validate_motion(999)
        assert valid is True
        assert safe_speed <= 100

        # Negative speed should be clamped to 0
        valid_neg, safe_neg, _ = controller._validate_motion(-50)
        assert valid_neg is True
        assert safe_neg == 0

    def test_servo_channel_bounds(self):
        controller = RobotController()
        with pytest.raises(ValueError):
            controller.set_servo(-1, 90)

        with pytest.raises(ValueError):
            controller.set_servo(16, 90)

        # Valid channels
        assert controller.set_servo(0, 90) is True
        assert controller.set_servo(15, 180) is True

    def test_pca9685_driver_bounds(self):
        pca = PCA9685()
        with pytest.raises(ValueError):
            pca.set_pwm(16, 0, 150)

        with pytest.raises(ValueError):
            pca.set_pwm(-1, 0, 150)

        # Valid PWM call in simulation
        assert pca.set_pwm(0, 0, 300) is True
        assert pca.stop_channel(0) is True

    def test_tb6612_emergency_stop_check(self):
        comm = DummyComm()
        tb = TB6612Controller(esp32_comm=comm)
        tb.emergency_stop()
        assert tb._emergency_stopped is True

        # Forward must not transmit robot move command
        tb.forward(50)
        assert "ROBOT_FWD 50" not in comm.sent_commands

        tb.clear_emergency_stop()
        assert tb._emergency_stopped is False
        tb.forward(50)
        assert "ROBOT_FWD 50" in comm.sent_commands
