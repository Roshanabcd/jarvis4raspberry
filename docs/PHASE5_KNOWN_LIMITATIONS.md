# JARVIS OS — Phase 5 Known Limitations & Boundaries
## Operational Boundaries, Hardware Constraints & Activation Guidance

---

# 1. Unauthenticated Coding Agents

### 1.1 Anthropic Claude Code (`claude`)
- **Current Status:** `UNAUTHENTICATED`
- **Cause:** Claude Code requires OAuth authentication with an Anthropic console account or API key.
- **Impact:** Claude Code is discovered and visible in the dashboard with its CLI path, but `MultiAgentOrchestrator` will not route active repairs to it until authenticated.
- **Resolution:** Run `claude auth login` in a local terminal window (`DISPLAY=:0`), complete the browser prompt, and click "Refresh Discovery" in JARVIS OS AI Agent Manager.

### 1.2 OpenCode Community CLI (`opencode`)
- **Current Status:** `UNAUTHENTICATED`
- **Cause:** No remote integration endpoints (OpenAI, DeepSeek, or Anthropic) are configured in `~/.opencode/`.
- **Impact:** Routed only if configured with local or external keys.

---

# 2. Hardware & Resource Limits (Raspberry Pi 5)

### 2.1 Local LLM Inference Speeds
- Local reasoning via Ollama (`llama3.2:1b`) on quad-core Cortex-A76 achieves ~18-24 tokens/sec.
- For complex multi-file repairs, `Antigravity` (`agy` with `gemini-3.8-flash-high`) or `Codex` (`codex` with `gpt-4o`) provides sub-second responses, whereas local 4B models may take 10-25 seconds.
- JARVIS OS intelligently scores cloud-backed agents higher for fast interactive code modifications while preserving Ollama as an offline fallback.

### 2.2 System Memory Safeguards
- Running VS Code, Google Chrome, and local Ollama simultaneously consumes ~4.2 GB of the 8 GB LPDDR4X RAM.
- JARVIS OS monitors available RAM and caps agent context token lengths to prevent triggering the Linux kernel OOM killer.

---

# 3. Security & Safety Exclusions

### 3.1 Robot Motors & Physical Actuators
- Physical robot actuators (`robot_move`, `servo_set`) are **strictly excluded** from autonomous agent permissions under all profiles.
- If a debugging task accidentally triggers a hardware motion command, the permission manager halts execution immediately.

### 3.2 Firmware & Flashing Tools
- Microcontroller flashing utilities (`esptool`, `avrdude`, `flashrom`) are permanently blocked by the hard-deny gate.
- Microcontrollers must be flashed intentionally through dedicated hardware tools, never autonomously by an AI agent.
