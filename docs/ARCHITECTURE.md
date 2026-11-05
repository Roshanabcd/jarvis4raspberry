# JARVIS OS — System Architecture & Component Design

## 1. High-Level Architecture Overview

JARVIS OS is a modular, event-driven AI operating environment engineered for the Raspberry Pi 5 (8GB RAM, ARM64) and robotics peripherals.

```mermaid
flowchart TD
    User([User Voice / Web / CLI]) --> UI[FastAPI REST / WS / Dashboard]
    UI --> Brain[JARVIS Brain Orchestrator]
    
    subgraph AI Engine
        Brain --> FP[Fast-Path Deterministic Engine <5ms]
        Brain --> MR[Model Router]
        MR --> Ollama[Local Ollama: llama3.2:1b / qwen3.5:4b]
        MR --> CloudAI[Cloud AI: Gemini / OpenAI / Anthropic]
    end

    subgraph Voice Pipeline
        Mic[Microphone / ReSpeaker] --> STT[Whisper STT / ALSA]
        STT --> Wake[Wake Word Detector: 'jarvis']
        Wake --> Brain
        Brain --> Cloner[Gradio Voice Cloner]
        Cloner -.->|Fallback| LocalTTS[espeak / pyttsx3 / simulated]
        Cloner --> Playback[Audio Output / aplay]
    end

    subgraph Robotics & Hardware
        Brain --> RobotCtrl[RobotController: Armed / E-Stop Gates]
        RobotCtrl --> ESP32[ESP32-S3 Serial Coprocessor]
        ESP32 --> TB6612[2x TB6612FNG Dual Drivers]
        TB6612 --> Motors[4x GA12-N20 DC Motors & Encoders]
        RobotCtrl --> PCA[Waveshare PCA9685 16-Ch PWM]
        PCA --> Servos[Pan-Tilt & Arm Servos]
    end

    subgraph Sensors & Vision
        Brain --> Vision[VisionService: rpicam-still / picamera2]
        Vision --> Cam[RPi Camera Module 3: imx708]
        Brain --> SensorMgr[SensorManager: BME280 / BH1750 / VL53L0X / PIR / HC-SR04]
    end

    subgraph Storage & Security
        Brain --> Tools[Tool Registry & Secure Sandbox]
        Brain --> MemDB[WAL SQLite Memory Store: 9 Categories]
        Tools --> Audit[Rotating JSONL Audit Log]
    end
```

---

## 2. Subsystem Breakdown

### A. Core Backend & Lifecycle (`apps/core/main.py`)
- FastAPI ASGI server running on Uvicorn.
- Lifespan context manager gracefully initialises SensorManager, VoiceService daemon, TaskScheduler, and RobotStateMachine.
- Clean shutdown stops background threads, disarms actuators, releases PWM outputs safely, and closes database connections.

### B. Hybrid Intelligence & Fast-Path Routing (`ai/brain.py`, `ai/local_engine.py`)
- **Fast-Path Engine**: Deterministic classification (<5ms) for time-critical commands: robot motion, sensor polling, emergency stop, math calculations, and system status queries.
- **Neural Reasoning Engine**: Local Ollama (`llama3.2:1b` / `qwen3.5:4b`) or cloud LLMs (Gemini 2.0 Flash / OpenAI GPT-4o-mini / Claude 3 Haiku) for conversational dialogue and open-domain knowledge.
- **Tool Calling Loop**: Multi-turn execution with a 5-round ceiling to prevent infinite recursion.

### C. Voice & Cloned Speech (`apps/voice/`)
- Wake word detection via boundary regex with future hooks for Porcupine and openWakeWord.
- Transcription via OpenAI Whisper (tiny model on CPU) with dummy WAV simulation support.
- `GradioVoiceCloner`: Dynamically discovers endpoints from Gradio web applications, caches synthesized WAV phrases locally, checks WAV headers, and provides instant fallback to local TTS when offline.

### D. Vision & Camera (`apps/vision/`)
- Supports native `rpicam-still` / `rpicam-jpeg` direct binary capture under Debian 13 / Python 3.14.
- Captures on-demand JPEG frames (1280x720 or 640x480) with base64 encoding for AI vision description.

### E. Motion Control & Coprocessor Link (`tools/robotics/`, `hardware/`)
- Actuators boot in a DISARMED state.
- Emergency stop permanently locks motion until cleared.
- Commands framed via checksummed ASCII/JSON protocol to ESP32-S3.
- ESP32 hardware watchdog terminates motor PWM if Raspberry Pi communication is interrupted for >500ms.

### F. Persistent Memory & Security (`memory/`, `security/`)
- SQLite database configured in Write-Ahead Logging (WAL) mode for concurrency.
- 9 supported categories: `USER`, `PROJECT`, `ROBOT`, `SYSTEM`, `CONVERSATION`, `TASK`, `KNOWLEDGE`, `PREFERENCE`, `EVENT`.
- Secure command runner enforcing an allowlist of approved Linux binaries without `shell=True`.
- Workspace directory sandboxing preventing path traversal attacks.
