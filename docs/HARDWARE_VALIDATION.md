# JARVIS OS — Hardware Validation & Interface Guide

## 1. Hardware Detection Matrix (Raspberry Pi 5)

| Hardware Device | Detected on Bus | Operational Level | Notes |
| :--- | :--- | :--- | :--- |
| **RPi Camera Module 3** | CSI RP1 (i2c-11 @ 0x1a) | **HARDWARE VERIFIED** | Imx708 sensor detected; frame capture verified via `rpicam-still` (640x480 & 1280x720). |
| **SoC Thermal Monitor** | `/sys/class/thermal/thermal_zone0` | **HARDWARE VERIFIED** | Real temperature verified (48.5°C to 51.0°C). |
| **Host Storage & RAM** | NVMe/SATA USB3 (/dev/sda2) | **HARDWARE VERIFIED** | 8GB RAM, 155GB free storage. |
| **Seeed ReSpeaker Lite** | ALSA capture device | **SIMULATED** | USB mic not plugged in. Pipeline tested via synthetic audio mock. |
| **Waveshare Servo HAT B**| I2C 0x40 | **SIMULATED** | Header I2C1 not active in boot config. Tested via driver mock. |
| **TB6612FNG Dual Drivers**| Relayed via ESP32-S3 | **SIMULATED** | Tested via level 1 software protocol mock. |
| **GA12-N20 Motors** | 12V 150RPM Encoders | **SIMULATED** | Requires separate physical power test when robot is propped up. |
| **BME280 Sensor** | I2C (Bus 1, 0x76/0x77) | **SIMULATED** | Driver loaded with Bosch compensation formula; ready for hardware scan. |
| **BH1750 Sensor** | I2C (Bus 1, 0x23) | **SIMULATED** | Driver loaded; ready for hardware scan. |
| **VL53L0X ToF Sensors (2x)**| I2C (Bus 1, 0x29) | **SIMULATED** | Requires XSHUT sequencing to disambiguate dual sensors. |
| **HC-SR04 Ultrasonic** | GPIO 23 (Trig), 24 (Echo) | **SIMULATED** | **CRITICAL**: Echo requires voltage divider (1kΩ/2kΩ) before connecting to Pi. |
| **HC-SR501 PIR** | GPIO 4 | **SIMULATED** | Digital input reading via gpiod / RPi.GPIO. |
| **ESP32-S3 DevKit** | USB Serial / `/dev/ttyAMA10` | **SIMULATED** | Packet protocol verified. Firmware sketch ready in `hardware/esp32/firmware/`. |

---

## 2. Electrical Wiring & Power Boundaries

### Safe Power Rails:
1. **Raspberry Pi 5 Power**:
   - MUST be powered strictly via official Raspberry Pi 27W USB-C PD power supply (5.1V / 5.0A).
   - NEVER back-feed power into Raspberry Pi 5 5V GPIO header pins from motor batteries or unconditioned supplies.
2. **Servo Power Supply**:
   - Servos (MG996R / SG90) draw up to 1.5A–2.5A peak stall current per motor.
   - Power MUST be connected to the Waveshare Servo HAT's dedicated external green screw terminal block (VIN / GND), NOT through the Pi's 5V rail.
3. **Motor Power Supply**:
   - GA12-N20 12V motors MUST be powered through the TB6612FNG `VM` pin connected to the 12V battery.
   - `VCC` logic pin on TB6612FNG must be supplied with 3.3V from the ESP32 or Raspberry Pi 3.3V rail.
4. **Ultrasonic Sensor 5V Echo Protection**:
   - HC-SR04 VCC is 5V, meaning the ECHO pin outputs a 5V logic signal.
   - Raspberry Pi 5 GPIO pins are strictly 3.3V tolerant and will be permanently damaged by 5V.
   - Use a voltage divider: 1kΩ from ECHO to Pi GPIO 24, and 2kΩ from Pi GPIO 24 to Ground.
5. **Dual VL53L0X Address Disambiguation**:
   - Both VL53L0X sensors boot up with default I2C address `0x29`.
   - Connect the XSHUT pin of Sensor 1 to GPIO 17 and Sensor 2 to GPIO 27.
   - Boot procedure: Pull both XSHUT LOW (standby) -> Bring Sensor 1 HIGH -> Write new address `0x30` via I2C -> Bring Sensor 2 HIGH at `0x29`.

---

## 3. Four-Level Actuator Test Hierarchy

To guarantee that no accidental motion occurs during automated tests, JARVIS OS enforces a strict 4-level test hierarchy:

- **Level 1 (Software Unit & Mock)**:
  - All automated CI and pytest suites run strictly at Level 1.
  - Motors and servos simulate state and write logs without asserting GPIO or serial commands.
- **Level 2 (Interface Discovery)**:
  - Read-only queries to `/dev/i2c*`, `/dev/tty*`, and `gpiodetect` without toggling actuator outputs.
- **Level 3 (Zero-Power Bench Check)**:
  - Logic cables attached, 12V battery power completely disconnected. Oscilloscope or logic analyzer confirms PWM signals without physical motion.
- **Level 4 (Physical Motion Validation)**:
  - Requires separate human supervision:
    1. Chassis elevated on a test stand with wheels raised off the surface.
    2. Emergency stop switch verified accessible.
    3. Explicit authorization via API `/api/robot/arm` or `./jarvis --arm`.
    4. Short duration (<= 2 seconds), low speed (<= 30%).
