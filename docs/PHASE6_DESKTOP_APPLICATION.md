# JARVIS OS — Phase 6 Desktop Application Specification

**System Architecture & Deployment Guide for Raspberry Pi 5 ARM64**

---

## 1. Overview & Strategy Selection

In Phase 6, JARVIS OS was transitioned from a browser-accessed web dashboard into a true Linux standalone desktop application.

### Evaluation of Desktop Shell Frameworks for Raspberry Pi 5
| Framework | Evaluation on Debian 13 ARM64 | Selected? | Technical Rationale |
| :--- | :--- | :--- | :--- |
| **Chromium App Shell (`--app=URL`)** | **Optimal** | **YES** | Pre-installed Google Chrome 157.0 with native hardware acceleration, PipeWire WebRTC audio routing, zero extra RAM overhead, frameless window mode (`--class=jarvis-os`), responsive 1360×768 window geometry. |
| **PyWebView** | Partial | Alternative | Requires PyGObject (`gi.repository.Gtk`) or Qt bindings which are not natively compiled inside the miniconda environment. |
| **Electron** | Poor | No | Adds 300+ MB of RAM overhead and slow cold-boot times on SBC Cortex-A76 CPU. |
| **Tauri** | Complex | No | Requires Rust toolchain and webkit2gtk compilation, high disk and memory footprint during builds. |

---

## 2. Desktop Launcher Architecture (`apps/desktop/launcher.py`)

The standalone desktop application is controlled by `apps/desktop/launcher.py` and wrapped by `/home/roshan/.local/bin/jarvis`.

### Core Lifecycle Flow:
1. **Single-Instance Enforcement:**
   - Acquires non-blocking file lock on `/home/roshan/.config/jarvis-os/desktop_app.lock`.
   - If an instance is already running, uses `xdotool search --class jarvis-os windowactivate` to bring the existing window to the front and terminates without spawning duplicate processes.
2. **Backend Health Inspection:**
   - Probes `http://127.0.0.1:8000/api/health`.
   - If inactive, automatically boots `apps.core.main:app` as a managed daemon process, writes PID to `~/.config/jarvis-os/backend.pid`, and polls until healthy.
3. **Application Window Launch:**
   - Launches Chrome in standalone app mode:
     `google-chrome --app=http://127.0.0.1:8000/ --class=jarvis-os --name=jarvis-os --window-size=1360,768 --user-data-dir=~/.config/jarvis-os/desktop-profile`
   - Strips browser address bars, tabs, bookmark bars, and navigation buttons.
   - Preserves PipeWire audio capture and playback permissions automatically via `--enable-features=WebRTCPipeWireCapturer --autoplay-policy=no-user-gesture-required`.
4. **Graceful Shutdown:**
   - Traps `SIGINT` and `SIGTERM`, releases file locks, and terminates subprocesses cleanly.

---

## 3. Desktop Entry Integration

- **Command-Line Executable:** `/home/roshan/.local/bin/jarvis` (accessible anywhere in terminal `PATH`).
  - `jarvis`: Launches standalone desktop GUI application.
  - `jarvis cli [cmd]`: Forwards to terminal CLI agent.
  - `jarvis --status`: Returns JSON status of desktop window and backend.
  - `jarvis --stop`: Safely terminates desktop window and backend services.
- **Application Menu Entry:** `/home/roshan/.local/share/applications/jarvis-os.desktop`.
- **Desktop Shortcut:** `/home/roshan/Desktop/jarvis-os.desktop` (double-clickable, executable permissions).
- **Application Icon:** High-resolution futuristic neon cyan arc-reactor emblem installed at `/home/roshan/.local/share/icons/hicolor/256x256/apps/jarvis-os.png`.
