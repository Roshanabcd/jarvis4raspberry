# JARVIS OS — Phase 2 Desktop Application Launching Guide
## Specification and Operational Guide for Desktop Application and Project Launching

### 1. Overview
The JARVIS Desktop Application Launcher (`tools/desktop/app_launcher.py`) and Project Manager (`tools/desktop/project_manager.py`) provide robust mechanisms to discover, launch, and verify GUI applications on the active X11 desktop (`DISPLAY=:0`).

### 2. Discovered Applications & Execution Syntax

| Application | Verified Executable Path | Launch Command Syntax | Verification Method |
| :--- | :--- | :--- | :--- |
| **Google Chrome** | `/usr/bin/google-chrome` | `google-chrome --new-window <url>` | Process PID, `wmctrl` window title |
| **Mozilla Firefox** | `/usr/bin/firefox` | `firefox --new-window <url>` | Process PID, `wmctrl` window title |
| **Visual Studio Code** | `/home/roshan/.local/bin/code` | `code --new-window <project_path>` | Process PID, `wmctrl` window title |
| **Google Antigravity** | `/home/roshan/Downloads/Antigravity-arm64/antigravity` | `antigravity <project_path>` | Process PID, `wmctrl` window title |
| **LXTerminal** | `/usr/bin/lxterminal` | `lxterminal --working-directory <path>` | Process PID |
| **PCManFM File Manager** | `/usr/bin/pcmanfm` | `pcmanfm <directory>` | Process PID, `wmctrl` window title |

### 3. Natural Language Commands Supported

* **Application Launching:**
  * *"Open Google Chrome."* / *"Open Chrome in a new window."*
  * *"Open Firefox."*
  * *"Open VS Code."*
  * *"Open Antigravity."*
  * *"Open Terminal."*
* **Project Opening:**
  * *"Open my GameProject in VS Code."*
  * *"Open my JARVIS project in Antigravity."*
  * *"Open my Unity project in VS Code."*
  * *"Open GameProject."*
* **Browser Navigation:**
  * *"Open YouTube in Google Chrome."*
  * *"Open GitHub in Firefox."*
  * *"Play relaxing music on YouTube."*
  * *"Search YouTube for robotics tutorials."*

### 4. Process Detachment & Environment Safety
All GUI processes are spawned with:
- `DISPLAY=:0` (native X11 desktop environment).
- `XAUTHORITY=/home/roshan/.Xauthority` (authenticated user session).
- `preexec_fn=os.setsid` (process group detachment, ensuring GUI windows remain active and decoupled from backend HTTP request cycles).
- Never run as root (`UID 1000: roshan`).
