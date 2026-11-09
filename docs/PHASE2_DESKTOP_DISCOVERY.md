# JARVIS OS — Phase 2 Desktop Environment Discovery

## 1. System & Session Profile
* **Host Platform:** Raspberry Pi 5 (8 GB RAM, ARM64 / AArch64)
* **Kernel & OS:** Linux Debian 13 Trixie (`6.18.60-1+rpt1`)
* **User Context:** `roshan` (UID 1000, GID 1000)
* **Home Directory:** `/home/roshan`
* **Desktop Session Type:** Native **X11** (`XDG_SESSION_TYPE=x11`, `DISPLAY=:0`)
* **Runtime Directory:** `/run/user/1000`
* **Wayland Status:** Not active (`WAYLAND_DISPLAY` is unset). X11 window management and automation APIs are natively available.

## 2. Discovered Desktop Applications & Executables

### Web Browsers
* **Google Chrome:**
  * Primary Path: `/usr/bin/google-chrome`
  * Stable Binary: `/usr/bin/google-chrome-stable`
  * Status: Installed and verified functional.
* **Mozilla Firefox:**
  * Primary Path: `/usr/bin/firefox`
  * Status: Installed and verified functional.
* **Default Desktop Opener:** `/usr/bin/xdg-open`

### IDEs & Code Editors
* **Visual Studio Code:**
  * CLI Executable: `/home/roshan/.local/bin/code`
  * Version: `1.141.2` (ARM64)
  * Launch Syntax: `/home/roshan/.local/bin/code --new-window <path>`
  * Status: Verified working.
* **Google Antigravity IDE:**
  * App Binary: `/home/roshan/Downloads/Antigravity-arm64/antigravity`
  * Pi-Apps Package: `/home/roshan/pi-apps/apps/Antigravity`
  * Launch Syntax: `DISPLAY=:0 /home/roshan/Downloads/Antigravity-arm64/antigravity <path>`
  * Status: Verified present on disk with Electron ARM64 runtime.

### Terminal & Shell Applications
* **Default Terminal:** `/usr/bin/x-terminal-emulator`
* **Desktop Terminal:** `/usr/bin/lxterminal`
* **Standard X11 Terminal:** `/usr/bin/xterm`

### Window Management & GUI Automation Utilities
* **wmctrl:** `/usr/bin/wmctrl` (Installed). Supports window querying, desktop geometry, window activation (`-a`), and title extraction.
* **xdotool:** `/usr/bin/xdotool` (Installed). Supports active window queries (`getactivewindow`, `getwindowname`), window focusing, and key/mouse actions.
* **File Manager:** `/usr/bin/pcmanfm` (LXDE default file manager).

## 3. Discovered Workspace Paths
* `/home/roshan/Downloads` (active workspace with multiple projects and tools)
* `/home/roshan/Desktop` (active desktop surface)
* `/home/roshan/.gemini/antigravity/scratch/jarvis-os` (active JARVIS OS repository)
* Target Workspace Support: Supports resolving and configuring `~/UnityGameWorkspace`, `~/Downloads`, and project directories.

## 4. Automation Strategy for Phase 2
1. **Application Launching:** Use `subprocess.Popen` running under user `roshan` with `DISPLAY=:0` and `XAUTHORITY=/home/roshan/.Xauthority`.
2. **Window Verification:** Use `wmctrl -l -p` and `xdotool` to verify that applications create windows on X11 rather than assuming success.
3. **Terminal Sessions:** Execute commands natively via `subprocess.Popen` with session-specific directory tracking and PTY or pipe capture.
4. **Security Confirmation:** Guard privileged operations (`sudo`, `rm -rf`, file overwriting) with approval tokens.
