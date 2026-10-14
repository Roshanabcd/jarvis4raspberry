# API
Endpoints:
- `/api/system` - System telemetry and status
- `/api/voice/command` - Voice command execution
- `/api/vision/capture` - Vision frame capture
- `/api/robot/*` - Robotics control (forward, stop, estop, servo)
- `/sensors/all` & `/api/sensors/all` - Read all sensor telemetry
- `/sensors/status` & `/api/sensors/status` - Operational status for all sensors
- `/sensors/{name}` & `/api/sensors/{name}` - Read specific sensor (bme280, bh1750, vl53l0x, hcsr501, hcsr04, pir, ultrasonic, lux, etc.)
- `/sensors/{name}/status` - Specific sensor operational status
- `/sensors/{name}/calibrate` - Calibrate sensor

