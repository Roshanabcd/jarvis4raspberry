# JARVIS OS — Product Requirements Document (PRD) & Task Master

## Project Overview
Transform JARVIS OS into a robust, high-performance, edge-first AI operating environment and physical robot platform on Raspberry Pi 5.

---

## Master Phase Checklist (Ralph Loop Tracker)

- [x] **PHASE 0: Backup, System Inspection & Diagnostics**
  - [x] Host discovery (Debian 13 Trixie, aarch64, Pi 5 8GB, NVMe SSD)
  - [x] Hardware verification (IMX708 Camera, Seeed ReSpeaker Lite USB, Simulation mode for unpinned I2C/Serial)
  - [x] Ollama daemon inspection (port 11434, llama3.2:1b and qwen3.5:4b models detected)
  - [x] Write `docs/JARVIS_PHASE0_DIAGNOSTIC.md` and `IMPLEMENTATION_PROGRESS.md`

- [x] **PHASE 1: Fix AI Chat Engine & Multi-Provider Architecture**
  - [x] Dynamic Ollama connection, streaming chat API (SSE/WebSocket), model switching (`llama3.2:1b` vs `qwen3.5:4b`)
  - [x] Multi-provider registry (Ollama, Gemini, OpenAI, Anthropic, NVIDIA NIM, OpenAI-compatible)
  - [x] Provider routing, fallback logic, telemetry (TTFT, tokens/sec)
  - [x] Chat UI repair (streaming responses, markdown/code rendering, model selector, cancel/retry)

- [x] **PHASE 2: Agent Tool Registry & Autonomous Execution**
  - [x] Typed tool registry with JSON Schema and validation
  - [x] System, Robot, Sensor, Vision, Memory, Productivity, Research, Application tool suites
  - [x] Autonomous tool calling loop with multi-round execution & error recovery

- [ ] **PHASE 3: ReSpeaker Lite Audio Capture & Wake-Word Engine**
  - [ ] PipeWire/ALSA low-latency audio capture via Seeed ReSpeaker Lite
  - [ ] Wake-word detector ("JARVIS") without device locking conflicts
  - [ ] Local & cloud speech-to-text (STT) pipeline with fallback

- [ ] **PHASE 4: OmniVoice Cloned Speech & Voice Pipeline**
  - [ ] OmniVoice Hugging Face Space & Gradio client adapter
  - [ ] Local reference voice (`data/voice_samples/myvoice.wav`) binding
  - [ ] SHA-256 caching and neural fallback (`edge-tts` / `en-GB-RyanNeural`)

- [ ] **PHASE 5: Real-Time Full-Duplex Audio & Voice Conversation Loop**
  - [ ] Audio playback through ReSpeaker Lite speaker via PipeWire
  - [ ] Barge-in / interruption handling & audio ducking
  - [ ] Unified voice interaction loop (Wake Word -> STT -> Agent Brain -> Cloned TTS -> Speaker)

- [ ] **PHASE 6: 14-App JARVIS Suite Implementation**
  - [ ] App 1: Home / Command Center
  - [ ] App 2: AI Chat
  - [ ] App 3: Voice Center
  - [ ] App 4: AI Studio
  - [ ] App 5: Vision Center
  - [ ] App 6: Robot Control
  - [ ] App 7: Sensors Center
  - [ ] App 8: Memory & Knowledge
  - [ ] App 9: Automations & Workflows
  - [ ] App 10: Tools & Skills
  - [ ] App 11: Integrations
  - [ ] App 12: System Monitor
  - [ ] App 13: Logs & Diagnostics
  - [ ] App 14: Settings Center

- [ ] **PHASE 7: Interactive Settings Center (Categories A–P)**
  - [ ] Complete UI & API endpoints for Categories A through P
  - [ ] Persistent storage in `config/config.yaml` and `.env` with atomic writes & schema validation

- [ ] **PHASE 8: Backend API & Database Hardening**
  - [ ] Full REST & WebSocket API coverage
  - [ ] SQLite WAL database optimizations & schema migrations

- [ ] **PHASE 9: Futuristic Responsive Frontend Redesign**
  - [ ] Dark navy & neon cyan aesthetic, responsive grid, zero UI lockups

- [ ] **PHASE 10: Robotics Hardware Safety Integration**
  - [ ] Disarmed boot state, latched e-stop, hardware detection with graceful simulation fallback

- [ ] **PHASE 11: Security, Privacy & Reliability**
  - [ ] Watchdog daemon, resource isolation, credential sanitization

- [ ] **PHASE 12: Automated Test Suite & Regression Testing**
  - [ ] Pytest verification across all units, APIs, and pipelines (target: 100% pass)

- [ ] **PHASE 13: Systemd Service & Auto-Recovery Setup**
  - [ ] Production systemd daemon configuration, health monitoring

- [ ] **PHASE 14: Final End-to-End Acceptance Verification**
  - [ ] Verification of Tests A through F

- [ ] **PHASE 15: Documentation & Milestone Reports**
  - [ ] Final comprehensive audit and architecture documentation
