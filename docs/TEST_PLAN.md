# JARVIS OS — Automated Test Plan

## 1. Testing Strategy & Principles
- **ARM64 Native Execution**: Runs directly on Raspberry Pi 5 under Linux aarch64.
- **Fail-Safe Actuation**: Automated tests MUST NEVER command unvalidated physical actuator motion.
- **Hardware Isolation**: Tests gracefully fallback to mocks/simulators when peripheral buses or cloud endpoints are unreachable.
- **Determinism**: 100% reproducible test suite with zero flakiness.

---

## 2. Test Suites Overview

### Suite 1: Actuator Safety & Locking (`tests/hardware/test_actuator_safety.py`)
- Disarmed startup verification (`robot.armed == False`).
- Movement rejection when disarmed.
- Arming and disarming mechanics.
- Emergency stop lockout: motion blocked until e-stop cleared.
- Speed clamping to `[0, 100]`.
- Servo channel bounds (`0 <= ch <= 15`) and PCA9685 duty cycle bounds (`0 <= pulse <= 4095`).
- TB6612 e-stop transmission check.

### Suite 2: ESP32-S3 Serial Protocol (`tests/hardware/test_esp32_protocol.py`)
- CRC8 checksum computation and consistency.
- Packet framing `$CMD:<seq>:<cmd>*<crc>`.
- Bidirectional ACK parsing.
- Telemetry packet extraction (`$TEL:<l>:<r>:<batt>*<crc>`).
- Firmware version handshake.
- Malformed byte stream resilience.

### Suite 3: Voice Subsystem & Gradio Voice Cloning (`tests/voice/`)
- Audio manager device detection and ALSA formatting.
- Wake word regex boundary and substring detection.
- STT silent dummy WAV generation and Whisper fallback.
- Local TTS synthesis.
- Conversation session tracking, timeout, and JSON serialization.
- Gradio custom voice cloner:
  - 404 / offline server detection.
  - Automatic fallback to local TTS engine.
  - Audio phrase caching with SHA256 hashes.
  - Binary header format verification (WAV, MP3, OGG).
  - Stop playback safety.

### Suite 4: Camera & Vision (`tests/vision/test_vision.py`)
- Simulation mode capture and frame structuring.
- Camera status metadata inspection.
- Scene description and object detection fallbacks.
- Hardware capture verification on Raspberry Pi Camera Module 3 (`imx708`) via native `rpicam-still`.

### Suite 5: Environmental Sensors (`tests/hardware/test_sensors.py`)
- SensorManager instantiation and alias resolution.
- BME280 temperature, pressure, humidity simulation and Bosch math.
- BH1750 ambient light lux parsing.
- VL53L0X distance reading.
- HC-SR501 PIR motion flag.
- HC-SR04 ultrasonic distance calculation.
- REST endpoints for sensors.

### Suite 6: Core System, API, Memory, & Encoders (`tests/unit/test_core.py`)
- ConfigManager YAML loading and fallbacks.
- MemoryDB CRUD, categories, indexing, and WAL mode.
- Robot state machine transitions and invalid transition rejections.
- FastAPI endpoints: `/api/system`, `/api/health`, `/api/robot/*`, `/api/memory/*`, `/api/vision/*`, `/api/chat`.
- Encoder odometry distance calculations and resets.
- System diagnostics metric keys and thermal checks.

### Suite 7: AI Intelligence & Router (`tests/unit/test_ai_system.py`, `tests/unit/test_brain.py`)
- Provider subclass validation.
- Ollama local inference adapter.
- OpenAI / Gemini / Anthropic cloud fallbacks.
- Deterministic fast-path execution (<5ms).
- Tool calling loop and execution safety.

### Suite 8: Tools & Security (`tests/unit/test_tools_and_security.py`)
- JSONL rotating audit logger with secret redaction.
- Permission manager risk levels (0 to 4) and confirmation gates.
- Tool registry 5-step validation pipeline.
- FileTools workspace confinement (path traversal prevention).
- Secure command runner argument denylist.
- Task scheduler SQLite persistence.
