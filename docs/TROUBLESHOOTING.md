# JARVIS OS — Troubleshooting & Diagnostics Guide

## 1. Quick Diagnostic Check
Run the non-destructive system health-check:
```bash
./scripts/healthcheck.sh
```
Or check via CLI:
```bash
./jarvis --status
./jarvis --sensors
```

---

## 2. Common Issues & Solutions

### A. Camera Module 3 Not Found or Failing
- **Symptom**: `rpicam-hello --list-cameras` reports "No cameras available".
- **Cause 1**: Ribbon cable seated backwards or loose.
  - *Fix*: Raspberry Pi 5 uses a 22-pin 0.5mm pitch FFC cable on CAM/DISP0 or CAM/DISP1. The blue pull-tab / stiffener faces away from the board latch.
- **Cause 2**: `camera_auto_detect=1` missing in `/boot/firmware/config.txt`.
  - *Fix*: Verify `cat /boot/firmware/config.txt | grep camera_auto_detect` has `camera_auto_detect=1`.

### B. Custom Voice Cloning (Gradio Live Link 404 / Offline)
- **Symptom**: `https://13f7044a4e78090fd2.gradio.live/` displays "No interface is running" or HTTP 404.
- **Cause**: Gradio `.live` public share tunnels expire automatically after 72 hours.
- **Resolution**:
  1. Restart your voice cloning notebook/server to obtain a new `.gradio.live` link (or host permanently on Hugging Face Spaces or a local GPU machine).
  2. Set the new link in `.env`:
     ```bash
     GRADIO_VOICE_URL=https://<your-new-hash>.gradio.live/
     ```
  3. JARVIS OS will automatically detect the new endpoint schema and use it. In the meantime, JARVIS automatically uses local TTS (espeak / pyttsx3 / simulated), ensuring zero interruption.

### C. I2C Devices Not Detected (`/dev/i2c-1` Missing)
- **Symptom**: `i2cdetect -y 1` returns "No such file or directory".
- **Cause**: I2C1 (GPIO 2 and 3) is disabled in the Raspberry Pi kernel device tree.
- **Fix**:
  1. Run `sudo raspi-config` -> Interface Options -> I2C -> Enable.
  2. Or add `dtparam=i2c_arm=on` to `/boot/firmware/config.txt` and reboot.

### D. Robot Refuses to Move (`Cannot move: Actuators are DISARMED`)
- **Symptom**: `forward()`, `backward()`, or API commands return 400 with "Actuators are DISARMED".
- **Cause**: Safety gate active. Actuators boot disarmed to protect people and hardware.
- **Fix**: Explicitly arm the actuators before requesting movement:
  ```bash
  curl -X POST http://localhost:8000/api/robot/arm
  ```
  If emergency stop was triggered, clear it first:
  ```bash
  curl -X POST http://localhost:8000/api/robot/clear_estop
  curl -X POST http://localhost:8000/api/robot/arm
  ```

### E. ESP32 Serial Port Missing
- **Symptom**: ESP32 runs in simulation mode; `/dev/ttyUSB0` not present.
- **Cause**: ESP32-S3 DevKit not plugged into USB, or power-only USB cable used.
- **Fix**: Connect ESP32-S3 via a data-capable USB-C cable. Run `dmesg -w` while plugging in to identify device node (`/dev/ttyUSB0` or `/dev/ttyACM0`). Set in `.env`:
  ```bash
  ESP32_SERIAL_PORT=/dev/ttyUSB0
  ```

### F. Ultrasonic Distance Sensor Reports Constant Timeout
- **Symptom**: HC-SR04 reads 0cm or raises `TimeoutError`.
- **Cause**: ECHO pin missing voltage divider or connected to wrong GPIO pin.
- **Electrical Safety Reminder**:
  - Connect HC-SR04 VCC to 5V.
  - Connect Trig to Pi GPIO 23.
  - Connect Echo through a voltage divider: 1kΩ resistor in series with Echo -> Pi GPIO 24, and 2kΩ resistor from GPIO 24 to GND.
  - Connecting 5V directly to Raspberry Pi GPIO will fry the pin!
