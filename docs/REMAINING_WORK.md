# JARVIS OS — Remaining Work & Physical Robot Milestone Roadmap

**Audit Verdict:** `STATUS 2 — SOFTWARE COMPLETE, HARDWARE NOT FULLY VERIFIED`  
**Current State:** 100% of software is implemented, builds, and passes all 143 tests. RPi Camera Module 3, host diagnostics, and local Ollama neural brain are physically verified. Physical motor movement, physical servo actuation, and physical sensors require hardware attachment and bench testing.

---

## 1. Prioritized Remaining Problems

### HIGH Priority (Hardware & Remote Blockers)
1. **Remote Gradio Voice Cloning Link Expired:**
   - *Status:* The user-provided URL (`https://13f7044a4e78090fd2.gradio.live/`) is returning HTTP 404.
   - *Resolution Required:* Start the Gradio voice cloning server on your host machine or colab, generate a fresh `--share` URL (or set up a persistent tunnel via Cloudflare/ngrok), and update `config/config.yaml` (`voice.gradio_url`) or set `export GRADIO_VOICE_URL="https://your-new-url.gradio.live/"`.
2. **Physical ESP32-S3 Coprocessor Disconnected:**
   - *Status:* No USB serial device detected in `/dev/ttyUSB*` or `/dev/ttyACM*`.
   - *Resolution Required:* Plug the ESP32-S3 DevKit into one of the Raspberry Pi 5 USB ports using a data-capable USB-C cable. Flash the provided Arduino sketch `hardware/esp32/firmware/esp32_robot_controller.ino`.
3. **External I2C Bus 1 Inactive / Unpowered:**
   - *Status:* `i2cdetect -y 1` shows all addresses `--`. The Waveshare Servo HAT B and sensors (BME280, BH1750, VL53L0X) are not detected.
   - *Resolution Required:* Seat the Waveshare Servo HAT firmly onto the 40-pin GPIO header. Supply 5V-6V external power to the green screw terminal of the HAT. Check wiring of SDA (GPIO 2) and SCL (GPIO 3).

### MEDIUM Priority (Physical Sensor Wiring)
4. **Seeed ReSpeaker Lite USB Microphone Unattached:**
   - *Status:* `arecord -l` reports no capture devices.
   - *Resolution Required:* Plug the ReSpeaker Lite USB microphone array into a USB 2.0 port. Verify appearance in `lsusb` and `arecord -l`.
5. **HC-SR04 Voltage Divider Wiring:**
   - *Status:* Unwired.
   - *Resolution Required:* Construct a 1kΩ / 2kΩ resistor divider for each HC-SR04 ECHO pin before connecting to GPIO 24 to safeguard the Raspberry Pi 5 against 5V overvoltage.
6. **Dual VL53L0X XSHUT Wiring:**
   - *Status:* Unwired.
   - *Resolution Required:* Wire the XSHUT pins of the two ToF sensors to GPIO 17 and GPIO 27 to allow programmatic address reassignment (0x29 and 0x30).

---

## 2. Step-by-Step Actions to Reach Next Verified Milestone

Follow these sequential steps to transition from software simulation to full physical robot operation:

### Step 1: Connect Physical USB Devices
1. Plug the **Seeed Studio ReSpeaker Lite USB Microphone** into USB 2.0 port.
   ```bash
   lsusb
   arecord -l
   ```
2. Plug the **ESP32-S3 DevKit** into USB 3.0 port.
   ```bash
   ls -la /dev/ttyUSB* /dev/ttyACM*
   ```
3. Set serial port permissions:
   ```bash
   sudo usermod -a -G dialout roshan
   ```

### Step 2: Flash ESP32 Firmware
1. Open Arduino IDE or compile with `arduino-cli`:
   ```bash
   arduino-cli compile --fqbn esp32:esp32:esp32s3 hardware/esp32/firmware/esp32_robot_controller.ino
   arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32s3 hardware/esp32/firmware/esp32_robot_controller.ino
   ```

### Step 3: Power and Test I2C Bus 1
1. Attach the Waveshare Servo HAT B to the 40-pin GPIO header.
2. Connect external 5V-6V power to the green screw terminal (ensure logic ground is common).
3. Scan I2C bus:
   ```bash
   i2cdetect -y 1
   ```
   *Expected output:* Address `0x40` (PCA9685), `0x76` or `0x77` (BME280), `0x23` (BH1750), `0x29` (VL53L0X).

### Step 4: Level 4 Supervised Physical Motor Bench Test
1. **CRITICAL:** Place the robot chassis on a wooden block or stand so that all 4 rubber wheels spin freely in mid-air.
2. In `config/config.yaml`, switch:
   ```yaml
   simulation_mode: false
   ```
3. Restart the JARVIS service:
   ```bash
   sudo systemctl restart jarvis-core.service
   ```
4. Verify arming requirement in terminal:
   ```bash
   jarvis "arm robot"
   jarvis "robot move forward at speed 25"
   jarvis "stop robot"
   ```
5. Verify emergency stop cut:
   ```bash
   jarvis "emergency stop"
   ```
