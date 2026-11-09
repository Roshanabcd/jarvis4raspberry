# Phase 2 Verification — Runtime & System Baseline

**Date:** 2026-11-09  
**Platform:** Raspberry Pi 5 (8 GB RAM, ARM64 / AArch64)  
**Operating System:** Debian GNU/Linux 13 (Trixie)  
**Desktop Environment:** Native X11 (`DISPLAY=:0`), Openbox Window Manager, Resolution 1360x768  
**Repository Path:** `/home/roshan/.gemini/antigravity/scratch/jarvis-os`  
**Git Baseline Commit:** `65218ea8c873d25ec47694ec8dec4aee600c5d5b`  
**Branch:** `feat/jarvis-phase2-desktop-agent`  

---

## 1. System Hardware & Desktop Session Inspection

| Component | Detected Specification | Verification Command / Output |
| :--- | :--- | :--- |
| **SoC / Arch** | Broadcom BCM2712, 4x Cortex-A76, AArch64 | `uname -m` -> `aarch64` |
| **Total RAM** | 7.91 GB physical (8 GB LPDDR4X) | `free -h` |
| **Display Session** | Native X11 (Openbox) on `:0` | `xdpyinfo`, `wmctrl -m` -> `Openbox` |
| **Screen Resolution**| 1360 × 768 pixels | `xdpyinfo \| grep dimensions` -> `1360x768 pixels` |
| **Active User** | `roshan` (UID: 1000, GID: 1000) | `id -u` -> `1000` |

---

## 2. Audio Hardware & PipeWire Routing

- **Audio Capture Device:** Seeed Studio ReSpeaker Lite USB
  - ALSA: `card 2: Lite [ReSpeaker Lite], device 0: USB Audio`
  - PipeWire Source Node: `127. ReSpeaker Lite Analog Stereo` (Volume: 0.94, Active)
  - Active Stream: `pw-record` (PID 46478 / background audio capture engine) connected directly to `input_FL` and `input_FR`.
- **Audio Playback Device:** Seeed Studio ReSpeaker Lite USB
  - ALSA: `card 2: Lite [ReSpeaker Lite], device 0: USB Audio`
  - PipeWire Sink Node: `106. ReSpeaker Lite Analog Stereo` (Volume: 0.60, Default)
  - Hardware fallback: HDMI 0 (`card 0`) and HDMI 1 (`card 1`).

---

## 3. Local AI Brain (Ollama)

- **Ollama Host:** `http://127.0.0.1:11434` (Running natively as background daemon)
- **Active / Verified Models:**
  1. `llama3.2:1b` (Size: 1.32 GB, Format: GGUF, Quantization: Q8_0, 1.2B parameters, Fast reasoning default)
  2. `qwen3.5:4b` (Size: 3.39 GB, Format: GGUF, Quantization: Q4_K_M, 4.7B parameters, Deep reasoning / code specialist)

---

## 4. Application Runtime & Installed Targets

- **Core Server:** Uvicorn on `http://localhost:8000/` (FastAPI app)
- **Installed Target Applications:**
  - Google Chrome: `/usr/bin/google-chrome` (Present & Verified)
  - Mozilla Firefox: `/usr/bin/firefox` (Present & Verified)
  - VS Code: `/home/roshan/.local/bin/code` (v1.141.2 ARM64, Present & Verified)
  - Antigravity IDE: `/home/roshan/Downloads/Antigravity-arm64/antigravity` (Present & Verified)
  - Default Terminals: `/usr/bin/lxterminal`, `/usr/bin/xterm` (Present & Verified)
- **Workspace Repositories:**
  - Game Project: `/home/roshan/UnityGameWorkspace/GameProject`
  - JARVIS OS: `/home/roshan/.gemini/antigravity/scratch/jarvis-os`

---

## 5. Baseline Health Check

- `GET /api/status`: `{"status":"OK","service":"JARVIS OS","version":"0.1.0"}`
- `GET /api/desktop/apps`: 6 desktop targets recognized and mapped.
- `GET /api/terminal/sessions`: Default interactive terminal session initialized at `/home/roshan`.
- Background voice loop: Actively sampling from ReSpeaker Lite USB via PipeWire.
