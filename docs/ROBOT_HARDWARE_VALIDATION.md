# JARVIS OS — Physical Robot Hardware Validation & Safety Manual

**Target Hardware Architecture:** Wheeled Mobile Robot + Raspberry Pi 5 Coprocessor System  
**Audit Date:** November 7, 2026  
**Auditor Verification Level:** Phase 5 (Pi 5 Host Environment) & Phase 6 (Safety Constraints)

---

## 1. Physical Hardware Detection Matrix

Live detection conducted on the target Raspberry Pi 5 host:

| Hardware Component | Expected Interface | Detected Physical State | Operating Classification |
| :--- | :--- | :--- | :--- |
| **Host SBC (Raspberry Pi 5)**| 8 GB LPDDR4X, Cortex-A76 | BCM2712 Quad-Core @ 2.4 GHz | **PHYSICALLY VERIFIED** |
| **RPi Camera Module 3** | CSI RP1 (`imx708@1a`) | Detected on `/dev/video*` & `rpicam` | **PHYSICALLY VERIFIED** (Live JPEG captured) |
| **SoC Thermal Monitor** | Thermal Zone 0 | Real temperature read: 49.0°C–51.0°C | **PHYSICALLY VERIFIED** |
| **Host Storage & RAM** | USB 3.0 SATA (/dev/sda2) | 8 GB RAM, 147 GB free SSD | **PHYSICALLY VERIFIED** |
| **Seeed ReSpeaker Lite** | USB Audio Class (ALSA) | USB ID `2886:0019`, Card 2 `Lite`, live PipeWire capture streaming | **PHYSICALLY VERIFIED** (Live Audio stream verified) |
| **Waveshare Servo HAT (B)**| I2C Bus 1 (`0x40`) | I2C-1 scan returned all `--` | **NOT POWERED / UNSEATED (SIMULATED)** |
| **TB6612FNG Dual Drivers**| Relayed via ESP32-S3 | Software driver layer verified | **UNVERIFIED PHYSICALLY (SIMULATED)** |
| **4x GA12-N20 Motors** | 12V 150RPM Encoders | Encoder math & firmware verified | **UNVERIFIED PHYSICALLY (SIMULATED)** |
| **BME280 Sensor** | I2C Bus 1 (`0x76` / `0x77`)| Not detected on I2C-1 | **NOT DETECTED (SIMULATED)** |
| **BH1750 Light Sensor** | I2C Bus 1 (`0x23`) | Not detected on I2C-1 | **NOT DETECTED (SIMULATED)** |
| **Dual VL53L0X ToF Sensors**| I2C Bus 1 (`0x29` / `0x30`)| Not detected on I2C-1 | **NOT DETECTED (SIMULATED)** |
| **Dual HC-SR04 Sonar** | GPIO 23, 24 | Configured with voltage divider warning | **UNWIRED (SIMULATED)** |
| **HC-SR501 PIR** | GPIO 4 | Digital pin driver ready | **UNWIRED (SIMULATED)** |
| **ESP32-S3 DevKit** | USB Serial / `/dev/ttyUSB*`| No USB/ACM serial nodes detected | **NOT PLUGGED IN (SIMULATED)** |

---

## 2. Electrical Wiring & Power Isolation Boundaries

Before connecting physical batteries, drivers, or motors to the Raspberry Pi 5, the following strict electrical boundaries must be verified with a multimeter:

```
                  ┌───────────────────────────────────────────────┐
                  │          12V Li-Ion / LiPo Battery            │
                  └──────────────┬─────────────────┬──────────────┘
                                 │                 │
                                 ▼                 ▼
             ┌─────────────────────────┐     ┌─────────────────────────┐
             │ XY-3606 DC-DC Converter │     │  SmartElex Relay Switch │
             │  (Steps down to 5.1V)   │     │  (Master 12V Actuator)  │
             └───────────┬─────────────┘     └────────────┬────────────┘
                         │                                │
                         ▼                                ▼
             ┌─────────────────────────┐     ┌─────────────────────────┐
             │  Raspberry Pi 5 USB-C   │     │ TB6612FNG Motor VM Rail │
             │  (Logic Power Rail)     │     │ (High-Current 12V Rail) │
             └─────────────────────────┘     └─────────────────────────┘
                         ▲                                ▲
                         │  COMMON GROUND (GND) ONLY      │
                         └────────────────────────────────┘
                         (NO 12V VOLTAGE LEAKAGE TO PI 5)
```

### Critical Electrical Rules:
1. **Raspberry Pi 5 Power Isolation:**
   - Power the Pi 5 strictly through its USB-C port from a regulated 5.1V supply (official 27W adapter or tested XY-3606 buck converter).
   - **NEVER** apply 5V or 12V power into the 40-pin GPIO 5V/3.3V pins directly.
2. **Servo Power Isolation (Waveshare Servo HAT B):**
   - High-torque servos (MG996R / DS3218) draw peak stall currents of 1.5A to 2.5A per motor.
   - Power **MUST** be supplied to the green screw terminal labeled `VIN / GND` on the Servo HAT.
   - Do **NOT** power servos from the Raspberry Pi's 5V logic rail.
3. **HC-SR04 5V Echo Pin Protection:**
   - The HC-SR04 operates at 5V and outputs a 5V logic HIGH on the ECHO pin.
   - Raspberry Pi 5 GPIO pins are strictly 3.3V tolerant; direct 5V injection will permanently destroy the RP1 GPIO chip.
   - Connect a voltage divider:
     - 1kΩ resistor between HC-SR04 ECHO pin and Pi GPIO 24.
     - 2kΩ resistor between Pi GPIO 24 and Common Ground.
4. **Dual VL53L0X I2C Address Disambiguation:**
   - Both sensors default to I2C address `0x29` on power-up.
   - Wire Sensor 1 `XSHUT` pin to GPIO 17 and Sensor 2 `XSHUT` to GPIO 27.
   - Boot sequence:
     1. Pull GPIO 17 and GPIO 27 LOW (putting both sensors into hardware shutdown).
     2. Drive GPIO 17 HIGH (powers on Sensor 1 at default `0x29`).
     3. Send I2C command to reassign Sensor 1 to address `0x30`.
     4. Drive GPIO 27 HIGH (powers on Sensor 2 at default `0x29`).
     5. Both sensors now operate concurrently without bus collision.

---

## 3. Four-Level Actuator Test Hierarchy

To prevent runaway robots, sheared gearboxes, or physical injury, JARVIS OS enforces a strict 4-level test hierarchy:

### Level 1: Software Unit & Simulation (Current State)
- Status: **100% COMPLETE & VERIFIED**
- Logic and state machines execute with simulated actuators and virtual packet generators.
- No physical movement is possible.

### Level 2: Bus & Interface Discovery
- Read-only scanning of physical buses (`i2cdetect -y 1`, `ls /dev/ttyUSB*`).
- Verification that devices acknowledge on expected I2C addresses without asserting motor PWM.

### Level 3: Zero-Power Bench Check
- Logic lines (I2C, UART, GPIO) connected between Pi 5, ESP32, and motor drivers.
- **12V motor battery power disconnected.**
- Oscilloscope or logic analyzer verifies PWM pulse generation, frequency (50 Hz for servos, 1-20 kHz for motors), and direction pin state toggling.

### Level 4: Supervised Physical Motion Validation
- Conducted only when Level 1, 2, and 3 have passed.
- **Prerequisites for Level 4:**
  1. Robot chassis physically placed on an elevated bench stand with all 4 wheels suspended off the ground.
  2. Physical emergency stop switch or relay inline with the 12V battery.
  3. Robot armed explicitly via `/api/robot/arm` or `jarvis "arm robot"`.
  4. Movement command limited to test duration (<= 2 seconds) and low speed (<= 30%).

---

## 4. Physical Integration Readiness Checklist

- [x] Raspberry Pi 5 operating environment configured and tested
- [x] Camera Module 3 physically connected and verified capturing real frames
- [x] Software safety gate (armed requirement + latching e-stop) implemented and tested
- [x] ESP32-S3 Arduino C++ firmware written with 500ms communication watchdog
- [ ] Connect ESP32-S3 DevKit to Pi 5 via USB-C cable (verifies `/dev/ttyUSB0` or `/dev/ttyACM0`)
- [ ] Connect Waveshare Servo HAT B firmly to 40-pin header and supply 5V-6V to screw terminals
- [ ] Connect BME280, BH1750, and VL53L0X to I2C-1 bus and verify addresses with `i2cdetect -y 1`
- [ ] Plug Seeed ReSpeaker Lite USB microphone array into USB 2.0 port
- [ ] Build 1kΩ/2kΩ resistor divider for HC-SR04 echo pins
- [ ] Elevate robot chassis and execute Level 4 supervised motor verification
