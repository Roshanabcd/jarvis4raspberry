# ⚡ JARVIS OS
**Just A Rather Very Intelligent System**

A production-grade AI operating environment for **Raspberry Pi 5 8GB**.

---

## Overview

JARVIS OS is a persistent background service that:
- Listens for a **wake word** ("jarvis") via microphone
- Understands **natural language** commands
- Controls **robotics hardware** (DC motors via ESP32 + TB6612FNG, servos via PCA9685)
- Reads **environmental sensors** (BME280, BH1750, VL53L0X, HC-SR501, HC-SR04)
- Provides a **web dashboard** with live telemetry
- Stores **conversation memory** in SQLite (vector hooks ready)
- Runs all AI inference **locally via Ollama** with optional OpenAI fallback
- Operates fully in **simulation mode** when hardware is not connected

---

## Quick Start

```bash
# Clone and set up
git clone <repo> ~/jarvis-os
cd ~/jarvis-os
python3 -m venv venv && source venv/bin/activate
pip install -e .

# Configure
cp .env.example .env
# Edit .env to add API keys (optional — Ollama works offline)

# Run (simulation mode on by default)
uvicorn apps.core.main:app --host 127.0.0.1 --port 8000
# Dashboard → http://localhost:8000/
```

---

## Production Install (Raspberry Pi 5)

```bash
sudo bash scripts/install.sh
sudo systemctl start jarvis-core
sudo journalctl -u jarvis-core -f
```

---

## Architecture

```
Raspberry Pi 5 (JARVIS OS)
├── apps/
│   ├── core/main.py          ← FastAPI server + lifespan
│   ├── api/                  ← REST + WebSocket endpoints
│   ├── voice/                ← Wake word → STT → Agent → TTS pipeline
│   ├── vision/               ← Camera capture + AI description
│   └── dashboard/static/     ← Dark-themed web UI
├── ai/
│   ├── providers/            ← Ollama, OpenAI adapters
│   ├── router/               ← Task-based model routing
│   ├── agents/               ← MainAgent + specialized agents
│   └── prompts/              ← JARVIS personality
├── hardware/
│   ├── raspberry_pi/         ← System info, state machine, health
│   ├── pca9685/              ← I2C servo driver (simulation safe)
│   ├── esp32/                ← Serial comms (simulation safe)
│   ├── tb6612/               ← Motor abstraction
│   ├── motors/               ← Encoder odometry
│   ├── servos/               ← Angle-limited servo control
│   └── sensors/              ← BME280, BH1750, VL53L0X, PIR, HC-SR04
├── memory/
│   ├── long_term/database.py ← WAL-mode SQLite, 7 categories
│   ├── short_term/           ← Conversation session buffer
│   └── vector/               ← Vector memory hooks (ready to wire)
├── tools/
│   ├── robotics/controller.py← Unified robot control API
│   ├── scheduler/            ← SQLite-backed task scheduler
│   ├── filesystem/           ← Workspace-bounded file operations
│   ├── shell/                ← Allowlist-only command runner
│   ├── web_search/           ← DuckDuckGo + page fetch
│   └── registry.py           ← 7-step secure tool execution pipeline
├── security/
│   ├── audit/                ← JSONL rotating audit log
│   ├── permissions/          ← Risk level 0–4 gate
│   └── secrets/              ← .env loading (never in source)
├── config/
│   ├── config.yaml           ← Master config
│   ├── hardware.yaml         ← Hardware flags
│   ├── models.yaml           ← AI provider config
│   └── permissions.yaml      ← Tool risk levels
├── services/
│   └── jarvis-core.service   ← systemd unit
└── tests/                    ← 96 tests, 96 passing
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | Service status |
| GET | `/api/system` | CPU/RAM/disk/temp |
| GET | `/api/health` | Component health check |
| GET | `/api/sensors/all` | All sensor readings |
| GET | `/api/sensors/{name}` | Single sensor (bme280, pir, etc.) |
| GET | `/api/robot/state` | Current robot state |
| POST | `/api/robot/forward?speed=N` | Move forward |
| POST | `/api/robot/backward?speed=N` | Move backward |
| POST | `/api/robot/stop` | Coast stop |
| POST | `/api/robot/estop` | Emergency stop |
| POST | `/api/robot/servo` | Set servo angle `{"channel":0,"angle":90}` |
| GET | `/api/vision/capture` | Capture camera frame |
| GET | `/api/vision/describe` | AI scene description |
| POST | `/api/chat` | Chat with JARVIS `{"message":"..."}` |
| POST | `/api/voice/command` | Process voice text `{"text":"..."}` |
| POST | `/api/memory/store` | Store memory `{"category":"...","content":"..."}` |
| GET | `/api/memory/search?query=` | Search memories |
| GET | `/api/logs` | Audit log entries |
| WS | `/ws` | Live telemetry (2s interval) |

---

## Hardware Safety Rules

> ⚠️ **CRITICAL — READ BEFORE CONNECTING HARDWARE**

1. **NEVER** drive motors directly from Raspberry Pi GPIO pins
2. **NEVER** drive motors directly from ESP32 GPIO pins  
3. **NEVER** apply motor voltage (7V–12V) to any GPIO pin
4. **NEVER** connect HC-SR04 ECHO (5V) directly to Pi or ESP32 GPIO — use a voltage divider (1kΩ/2kΩ)
5. **ALWAYS** power servos from an external supply — the Pi 5V rail cannot source servo current
6. **DEFAULT** robot state after boot: **MOTORS OFF**
7. **DEFAULT** servo position: **HOME ANGLE (90°)**
8. Autonomous motion requires **explicit API authorization**

---

## Configuration

Edit `config/config.yaml`:

```yaml
simulation_mode: true     # Set false when hardware is connected
api_port: 8000
wake_word: "jarvis"       # Trigger phrase
```

Set secrets in `.env`:
```
OPENAI_API_KEY=sk-...        # Optional — for cloud AI
JARVIS_SECRET_KEY=...        # Dashboard auth key
```

---

## Simulation Mode

All hardware drivers fall back to simulation when `simulation_mode: true`:
- Sensors return realistic fixed values
- Motors log commands instead of driving hardware
- Camera returns a static scene description
- Voice uses `espeak` (or logs to console) instead of ReSpeaker

---

## Tests

```bash
./venv/bin/pytest tests/ -v
# 96 passed ✓
```

Test coverage:
- `tests/unit/test_core.py` — Config, Memory, State Machine, API, Encoders, Vision, RPi
- `tests/unit/test_ai_system.py` — AI providers, model router, agents, personality
- `tests/unit/test_tools_and_security.py` — Tool registry, command runner, scheduler, audit
- `tests/hardware/test_sensors.py` — All 5 sensors + manager + API
- `tests/voice/test_voice.py` — Audio, wake word, STT, TTS, conversation, voice service

---

## I2C Device Map (Raspberry Pi 5)

| Bus | Device | Address | Notes |
|-----|--------|---------|-------|
| `/dev/i2c-4` | PCA9685 Servo HAT | 0x40 | Waveshare Servo Driver HAT B |
| `/dev/i2c-4` | BME280 | 0x76/0x77 | Temp/Humidity/Pressure |
| `/dev/i2c-4` | BH1750 | 0x23 | Light sensor |
| `/dev/i2c-4` | VL53L0X | 0x29 | Time-of-flight distance |

---

## Connecting the ESP32-S3

The ESP32-S3 handles real-time motor PWM via TB6612FNG.

Serial port: `/dev/ttyAMA10` (current), `/dev/ttyUSB0` (when connected via USB)

Update `config/hardware.yaml`:
```yaml
esp32:
  port: /dev/ttyAMA10   # or /dev/ttyUSB0
  baud: 115200
```

---

## Voice Pipeline

```
Microphone (ReSpeaker)
  → AudioManager.record_audio()
  → SpeechToText.transcribe()   (Whisper tiny model)
  → WakeWordDetector.detect()   ("jarvis" keyword match)
  → MainAgent.handle()          (intent routing)
  → TextToSpeech.speak()        (espeak / pyttsx3)
```

Wake word detection uses keyword matching by default. Upgrade to Picovoice Porcupine or openWakeWord for production accuracy (see `apps/voice/wake_word.py`).

---

## License

MIT License — see LICENSE file.
# jarvis4raspberry
