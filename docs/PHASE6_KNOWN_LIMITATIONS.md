# JARVIS OS — Phase 6 Operational Boundaries & Known Limitations

**Factual Documentation of External Dependencies and Hardware Constraints**

---

## 1. Google Colab Gradio Tunnel Lifecycle
- **Limitation:** Google Colab public `.gradio.live` tunnels expire automatically after 72 hours, or whenever the Colab session disconnects due to inactivity or GPU preemption.
- **Remediation:** When Colab disconnects, JARVIS automatically switches to `Neural Fallback (Edge-TTS Ryan)` without interrupting conversational AI or desktop automation. When the user relaunches `Super_Eleven_Lab_Lite_2_1.ipynb`, they can paste the new URL into **Voice Center** -> **Connect & Register** or trigger the automated runner.

## 2. Raspberry Pi 5 CPU Inference Throughput
- **Limitation:** While Ollama `llama3.2:1b` generates at ~14-18 tokens/second once loaded into RAM, cold-loading model weights from the microSD/NVMe storage into LPDDR4X memory takes approximately 40-50 seconds on initial boot.
- **Remediation:** Fast-path deterministic commands (system status, calculations, camera captures, desktop actions) bypass the LLM and execute in <10ms. Once warmed up, conversational inference completes in 2-4 seconds.

## 3. Physical Hardware Safeguards
- **Actuators & Servos:** Robotic motors (TB6612) and servos (PCA9685) remain disarmed and in safe software lock state during Phase 6 desktop automation and voice testing.
- **System Master Volume:** PipeWire master sink volume is locked to 65% to protect the physical speaker drivers.
