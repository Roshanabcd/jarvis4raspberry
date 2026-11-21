# JARVIS OS Integration Guide — Module 31 (JARVIS Robot Brain)

## 1. Mounting Inside JARVIS OS Core
```python
from fastapi import FastAPI
from backend.app.config import RobotBrainConfig
from backend.app.main import mount_module
from backend.services.robot_brain_engine import RobotBrainEngine

jarvis_app = FastAPI(title="JARVIS OS Core")
m31_engine = RobotBrainEngine(RobotBrainConfig(db_path="./data/jarvis_robot_brain.db"))
mount_module(jarvis_app, engine=m31_engine, include_root_ui=False)
```
Mounted routes: `/api/v1/robot-brain/*`, `/api/v1/robot-brain/ws/telemetry`, `/robot-brain`, and `jarvis_app.state.robot_brain`.

## 2. Connecting Real Hardware (ROS2 / Raspberry Pi 5 GPIO / Serial)
Subclass `RobotHardwareAdapter` in `backend/adapters/hardware_adapter.py`:
- Set `adapter_name` (e.g., `"ros2_humble_diffdrive"` or `"rpi5_gpio_motor_hat"`).
- Set `is_simulated = False`.
- Implement `apply_velocity()` and `engage_estop()` to publish `/cmd_vel` Twist messages or drive PWM/serial motor controllers with hardware watchdog relays.
