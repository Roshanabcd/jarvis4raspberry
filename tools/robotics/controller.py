from config.config_manager import config
from hardware.pca9685.driver import PCA9685
from hardware.esp32.serial_comm import ESP32Controller
import logging

logger = logging.getLogger("JARVIS-ROBOTICS")

class RobotController:
    def __init__(self):
        self.simulated = config.get("simulation_mode", True)
        self.state = "IDLE"
        logger.info(f"RobotController initialized (Simulated={self.simulated})")
        
        self.servo_controller = PCA9685()
        self.motor_controller = ESP32Controller()

    def forward(self, speed: int = 100):
        self.state = "MOVING_FORWARD"
        if self.simulated:
            logger.info(f"[SIM] Moving forward at speed {speed}")
        else:
            self.motor_controller.send_command(f"MOTOR_FWD {speed}")

    def backward(self, speed: int = 100):
        self.state = "MOVING_BACKWARD"
        if self.simulated:
            logger.info(f"[SIM] Moving backward at speed {speed}")
        else:
            self.motor_controller.send_command(f"MOTOR_BWD {speed}")

    def turn_left(self, speed: int = 100):
        self.state = "TURNING_LEFT"
        if self.simulated:
            logger.info(f"[SIM] Turning left at speed {speed}")
        else:
            self.motor_controller.send_command(f"MOTOR_LEFT {speed}")

    def turn_right(self, speed: int = 100):
        self.state = "TURNING_RIGHT"
        if self.simulated:
            logger.info(f"[SIM] Turning right at speed {speed}")
        else:
            self.motor_controller.send_command(f"MOTOR_RIGHT {speed}")

    def stop(self):
        self.state = "STOPPED"
        if self.simulated:
            logger.info("[SIM] Stopping motors")
        else:
            self.motor_controller.send_command("MOTOR_STOP")

    def emergency_stop(self):
        self.state = "EMERGENCY_STOP"
        logger.error("!!! EMERGENCY STOP ACTIVATED !!!")
        if not self.simulated:
            self.motor_controller.send_command("ESTOP")

    def set_servo(self, channel: int, angle: int):
        # Rough translation of angle (0-180) to pulse width for standard 50Hz servos
        angle = max(0, min(180, angle))
        pulse = int(150 + (angle / 180.0) * 450)
        if self.simulated:
            logger.info(f"[SIM] Setting servo {channel} to {angle} degrees (pulse {pulse})")
        else:
            self.servo_controller.set_pwm(channel, 0, pulse)

robot = RobotController()
