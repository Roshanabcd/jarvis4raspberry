# JARVIS OS — Safety Architecture & Electrical Protocol

> ⚠️ **CRITICAL ROBOTICS SAFETY NOTICE**  
> Physical robotics hardware involves moving mechanical parts, high current draw, and potential electrical back-feed. Read and adhere to every safety rule below.

---

## 1. Golden Rules of Robotics Safety

1. **DISARMED BOOT STATE**:
   - Actuators boot in a strictly DISARMED state (`robot.armed = False`).
   - Movement commands will be rejected with an error unless the robot is explicitly armed.
2. **HARD EMERGENCY STOP LOCKOUT**:
   - Once emergency stop (`/api/robot/estop` or `robot.emergency_stop()`) is triggered, all PWM outputs are immediately cut to 0.
   - Movement commands are permanently locked out.
   - Emergency stop MUST be explicitly cleared via `/api/robot/clear_estop` before actuators can be re-armed.
3. **NEVER SWEEP ALL SERVOS ON STARTUP OR SHUTDOWN**:
   - Sweeping all 16 PCA9685 servo channels concurrently creates massive inrush current spikes (>10A) and can crush mechanical linkages or fingers.
   - On shutdown, servos are released (`stop_all()` / 0 duty cycle) to go limp safely without forced motion.
4. **NO DIRECT GPIO MOTOR DRIVING**:
   - Raspberry Pi GPIO pins source a maximum of 16mA. Attempting to power a DC motor or servo signal directly from Pi GPIO will destroy the RP1 chip.
   - Always route motor power through a TB6612FNG or similar dedicated motor driver IC.
5. **NEVER CONNECT 12V MOTOR POWER (VM) TO 5V OR 3.3V RAILS**:
   - The 12V robot battery MUST ONLY connect to TB6612FNG `VM` and ground.
   - Logic supply (`VCC`) on the TB6612 must be 3.3V.
6. **5V ECHO PIN VOLTAGE DIVIDER REQUIRED**:
   - HC-SR04 ultrasonic sensors output 5V on the ECHO pin.
   - Raspberry Pi 5 GPIO inputs are strictly 3.3V tolerant.
   - You MUST place a voltage divider (1kΩ and 2kΩ resistors) or logic-level shifter between the Echo pin and Pi GPIO 24.
7. **BENCH ELEVATION FOR MOTOR TESTING**:
   - When performing initial physical motor tests, elevate the robot chassis on a block or test stand so the wheels rotate freely in the air.
   - Keep a hand ready on the main battery switch or emergency stop button.

---

## 2. Safe Power Topology Diagram

```
       +-----------------------+
       |   12V Robot Battery   |
       +-----------+-----------+
                   |
         +---------+---------+
         | Main Power Switch |
         +---------+---------+
                   |
     +-------------+-------------+
     |                           |
     v (12V Motor Rail)          v (12V Input)
+--------------------+   +-----------------------+
|  2x TB6612FNG VM   |   |   XY-3606 DC-DC       |
|  (Left & Right)    |   |   Buck Converter      |
+---------+----------+   +-----------+-----------+
          | (High Current)           | (5V Logic)
          v                          v
  [ 4x GA12-N20 Motors ]   [ Waveshare Servo HAT ]
                           [ External Terminal   ]
                                     |
                                     v
                           [ SG90 / MG996R Servos ]

+-------------------------------------+
| Official 27W USB-C PD Power Adapter |
+------------------+------------------+
                   | (5.1V / 5.0A Dedicated)
                   v
        [ Raspberry Pi 5 USB-C ]
                   | (3.3V Logic & CSI / I2C / UART)
                   +--------> [ BME280 / BH1750 / VL53L0X Sensors ]
                   +--------> [ Pi Camera Module 3 ]
                   +--------> [ ESP32-S3 Logic VCC ]
```

---

## 3. Software Safety Guard Matrix

| Component | Software Guard | Behavior on Trigger |
| :--- | :--- | :--- |
| `RobotController` | Armed Flag Guard | Motion rejected if `armed=False`. |
| `RobotController` | E-Stop Latch Guard | Motion rejected if `state="EMERGENCY_STOP"`. |
| `RobotController` | Speed Clamping | Clamps target speed to `[0, 100]`. |
| `PCA9685` | Channel Validation | Throws `ValueError` if channel is outside 0–15. |
| `PCA9685` | Duty Cycle Clamping | Clamps pulse duration to 0–4095. |
| `ESP32 Firmware` | Watchdog Timer (500ms)| Automatically cuts PWM to 0 if Pi drops comms. |
| `SecureCommandRunner` | Command Allowlist | Rejects unapproved shell binaries. |
| `FileTools` | Workspace Confinement | Blocks directory traversal outside authorized folders. |
