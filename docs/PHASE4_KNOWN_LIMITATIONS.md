# JARVIS OS — Phase 4 Known Limitations & System Boundaries

## 1. Window System & Display Environment
- **Native X11 Requirement**: Active window querying (`xdotool getactivewindow`), mouse cursor movement, and key event injection operate via the X11 socket on `DISPLAY=:0`. In pure Wayland sessions without XWayland permissions enabled for non-root users, keystroke and mouse injection requires either uinput-level daemons (`ydotool`) or direct application automation APIs.
- **Root-Owned Window Protection**: Windows owned by system root processes cannot be synthetically minimized or resized by standard user privileges, which is handled gracefully by reporting permission status.

---

## 2. Multimodal Local Inference Speed
- **CPU Inference Boundaries on Raspberry Pi 5**: As established in Phase 4C, the local `qwen3.5:4b` Ollama model requires >60 seconds to process image tokens on the 4-core Cortex-A76 CPU. Consequently, interactive sub-second visual perception relies on native X11 window hierarchy analysis (`scrot`, `wmctrl`, `xprop`, `Pillow`) rather than end-to-end multimodal neural generation. Local vision models should be reserved for slow asynchronous offline analysis.

---

## 3. Transient Dynamic Layouts
- **Custom Hardware Renderers & Accelerated Canvases**: Applications rendering directly to full-screen OpenGL/Vulkan contexts (such as certain 3D games or video games in Unity) bypass X11 widget hierarchies. Semantic button classification on these canvases relies on relative visual template layouts rather than X11 subwindow geometry.
- **Pre-Roll YouTube Advertisements**: In Google Chrome, YouTube videos play within the active user session. When interacting with player controls (pause/resume/volume), shortcuts target the active media player element regardless of whether pre-roll advertisements or destination content are active.

---

## 4. Hardware Disarm Policy
- **Actuators Quarantined**: All physical robot hardware (ESP32, servo motors, chassis locomotion) remains disarmed and offline during Phase 4 computer-use operations.
