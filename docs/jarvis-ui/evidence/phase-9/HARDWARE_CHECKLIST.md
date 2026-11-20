# JARVIS OS Physical Hardware & Robotics Verification Checklist
**Phase 9 Safety Gate** · Operator-Executed Protocol

> [!CAUTION]
> Autonomous AI agents are strictly forbidden from issuing physical motion commands to real actuators or motors. This manual verification checklist must be executed directly by the human operator with the physical robot placed on an elevated stand or test bench.

---

## 1. Safety Pre-Flight Checks
- [ ] **Physical Elevation:** Robot chassis is elevated on a test block so wheels / treads cannot contact the desk or ground.
- [ ] **Power Isolation:** Battery switch is easily reachable; emergency stop latch is verified mechanically free of obstruction.
- [ ] **I2C Bus Wiring:** PCA9685 servo driver, BME280, BH1750, and VL53L0X connected to 3.3V/5V rails with common ground to Raspberry Pi 5.
- [ ] **Default Safe State:** Verify robot UI initially renders `DISARMED (SAFE)` with all directional motion buttons (`▲`, `◀`, `▶`, `▼`) disabled.

---

## 2. Emergency Stop Interlock Protocol
- [ ] **Emergency Stop Activation:** Click the large red `EMERGENCY STOP` button in the UI (`/futuristic/#robot`).
- [ ] **Visual Interlock Confirmation:** Verify banner flashes red with `EMERGENCY STOP LATCHED` and all PWM outputs immediately drop to 0V.
- [ ] **Backend Enforcement:** Attempt to call `/api/robot/forward` via terminal; verify backend returns HTTP 400 (`Cannot move: Emergency stop active`).
- [ ] **Clear E-Stop Authorization:** Click `Clear E-Stop`, enter Administrator PIN in the modal dialog, and confirm latch returns to `INACTIVE`.

---

## 3. Actuator Arming Verification
- [ ] **Arming Guard:** Click `Arm Actuators` button in the UI.
- [ ] **Admin PIN Authorization:** Enter valid Administrator PIN. Confirm banner updates to `ACTUATORS ARMED & READY`.
- [ ] **Disarm Test:** Click `Disarm Actuators`. Confirm UI immediately returns to `DISARMED` without requiring a PIN.

---

## 4. Simulated vs Physical Actuation Gating
- [ ] **Simulation Mode Labeling:** Verify the UI displays `SIMULATION MODE ACTIVE` banner whenever physical motor drivers are unattached.
- [ ] **Directional Kinematics:** While armed in simulation mode, click `Forward`, `Backward`, `Turn Left`, and `Turn Right`. Verify speed limits (10-100%) are honored.
- [ ] **Servo Pan/Tilt:** Adjust Channel 0 (Pan) and Channel 1 (Tilt) sliders between 0° and 180°. Verify smooth simulation response.

---

## 5. Environmental & Spatial Sensor Readings
- [ ] **BME280 Sensor:** Place finger near sensor; verify temperature readout changes within 2 seconds.
- [ ] **BH1750 Optical Sensor:** Cover sensor with hand; verify illuminance drops below 50 Lux. Shine light; verify lux rises above 500 Lux.
- [ ] **VL53L0X Laser Distance:** Place hand 100mm in front of sensor; verify range readout reflects distance in mm.
- [ ] **HC-SR04 Ultrasonic:** Verify distance reading adjusts between 2cm and 200cm.
- [ ] **HC-SR501 PIR:** Wave hand in front of PIR sensor; verify `ACTIVITY ALERT` is surfaced.

---

## Sign-Off
- **Operator Name:** _______________________________________
- **Date Verified:** _______________________________________
- **Outcome:** [ ] PASS  [ ] FAIL
- **Notes / Anomalies:** __________________________________
