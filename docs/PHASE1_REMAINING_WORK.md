# JARVIS OS — Phase 1 Remaining Work & Out-of-Scope Items

## 1. Phase 1 Objective Completion

Phase 1 ("BUILD THE REAL INTELLIGENT AI ASSISTANT") has met all 20 acceptance criteria specified in the architectural contract:
- Production conversational AI with Ollama `llama3.2:1b` (and `qwen3.5:4b` support).
- Stale and repeated response elimination through unique request, message, and session correlation.
- Exact response rendering without arbitrary truncation or summary substitution.
- Real hardware telemetry (accurate RAM GB values, Linux uptime, thermal zone temperature, and explicit robot states).
- Multi-task agent orchestration via `CompoundTaskOrchestrator`.
- 78 registered deterministic tools covering math, system info, date/time, files, and memory.
- Persistent SQLite conversation history with session isolation.
- Text-first streaming architecture decoupled from speech generation.

---

## 2. Intentionally Deferred Items (Out of Scope for Phase 1)

As strictly mandated by the Phase 1 instructions, the following capabilities were intentionally excluded and reserved for subsequent development phases:

1. **Physical Actuator Movement & Motor Arming:**
   - Physical robotics locomotion in physical space was preserved in simulation mode (`robot.simulated == True`) to ensure safety and prevent uncommanded physical robot movements during software AI stabilization.
   - Physical GPIO / I2C motor calibration will be addressed in Phase 2 (Physical Robotics & Hardware Integration).

2. **Desktop Screen Control & Unrestricted Automation:**
   - Unrestricted desktop screen inspection, mouse clicking, keyboard automation, and arbitrary shell execution were omitted per Phase 1 security guidelines.
   - Sandboxed desktop file navigation (`open_folder`, `open_file`) remains available under controlled parameters.

3. **Offline On-Device Neural Voice Cloning:**
   - While OmniVoice (via Google Colab Tesla T4 runner) and Edge-TTS Neural Fallback are operational, running 5 GB zero-shot voice cloning diffusion models directly on Pi 5 CPU remains deferred in favor of text-first performance.

---

## 3. Recommended Backlog for Phase 2

1. **Model Pre-warming Systemd Service:** Create an `ollama-prewarm.service` to pre-load `llama3.2:1b` into RAM on Raspberry Pi 5 boot, eliminating the 40-second cold-start latency for the very first user interaction.
2. **Vector Embeddings Store:** Integrate `sqlite-vec` or local mini-embeddings into `memory/vector/` for semantic similarity search over stored user memories.
3. **Hardware Sensor Bus Scanning:** Enable periodic background polling for I2C devices (BME280, BH1750, VL53L0X) to automatically transition robot and sensor states from `SIMULATION` to `CONNECTED` when physical sensors are attached to GPIO pins.
