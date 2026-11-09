# JARVIS OS — Phase 2 Desktop Architecture
## Architecture & Implementation Specification for Linux Desktop Automation on Raspberry Pi 5

### 1. Executive Summary
Phase 2 establishes the **JARVIS Desktop Agent** — a deterministic, authenticated local automation subsystem enabling natural-language desktop application launching, browser and YouTube navigation, VS Code and Antigravity IDE project management, bounded file and content searching, and interactive Linux terminal command execution on Raspberry Pi 5.

### 2. Architecture Overview

```
                      +-----------------------------+
                      |      JARVIS OS Brain        |
                      |   (LocalEngine / LLM)       |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |    Desktop Action Engine    |
                      |  (action_engine.py / Core)  |
                      +--------------+--------------+
                                     |
         +-------------------+-------+-------+--------------------+
         |                   |               |                    |
         v                   v               v                    v
+-----------------+ +-----------------+ +----------------+ +------------------+
|   App Launcher  | | Project Manager | |  File Search   | | Terminal Engine  |
| (Chrome, Code,  | |(VSCode / AGY IDE| | (Bounded Name/ | | (PTY/Subprocess,  |
| Antigravity...) | |Project Resolv.) | | Content Grep)  | | CWD, Conf. Gate) |
+--------+--------+ +--------+--------+ +--------+-------+ +--------+---------+
         |                   |                   |                  |
         +-------------------+---------+---------+------------------+
                                       |
                                       v
                      +----------------------------------+
                      |    Linux Kernel & X11 Desktop    |
                      |   (DISPLAY=:0, wmctrl, xdotool)  |
                      +----------------------------------+
```

### 3. Core Subsystems

#### 3.1 Desktop Action Engine (`tools/desktop/action_engine.py`)
Acts as the unified gateway for all desktop commands. Guarantees:
- Unique `action_id` generation for audit logging.
- Verification before completion: ensures process PID is tracked and top-level window appears on X11 display.
- Exact telemetry reporting: captures start time, end time, duration in milliseconds, exit status, and detailed error messages.

#### 3.2 Application Launcher (`tools/desktop/app_launcher.py`)
- Discovers verified system binaries for:
  - Google Chrome: `/usr/bin/google-chrome`
  - Mozilla Firefox: `/usr/bin/firefox`
  - Visual Studio Code: `/home/roshan/.local/bin/code`
  - Antigravity IDE: `/home/roshan/Downloads/Antigravity-arm64/antigravity`
  - Terminal: `/usr/bin/lxterminal`, `/usr/bin/x-terminal-emulator`
  - File Manager: `/usr/bin/pcmanfm`
- Executes processes under the logged-in user (`roshan`, UID 1000) with `DISPLAY=:0` and `XAUTHORITY=/home/roshan/.Xauthority`.
- Detaches child process groups via `os.setsid` so desktop applications remain active independently of backend service lifecycles.

#### 3.3 Project Manager (`tools/desktop/project_manager.py`)
- Scans configured workspace roots (`~/UnityGameWorkspace`, `~/Downloads`, `~`).
- Recognizes project markers (`.git`, `package.json`, `pyproject.toml`, `requirements.txt`, `Cargo.toml`, Unity `Assets/` and `ProjectSettings/`).
- Resolves project requests (`Open my Unity project in VS Code`, `Open my JARVIS project in Antigravity`).
- Launches the verified project path in the target IDE with `--new-window` support.

#### 3.4 Terminal Execution Engine (`tools/terminal/terminal_manager.py`)
- Manages persistent, interactive shell sessions with directory tracking (`cwd`).
- Supports shell expressions, pipes, redirection, and environment variables via Bash.
- Captures real standard output (`stdout`), standard error (`stderr`), exit code, and execution time.
- Enforces a **Security Confirmation Gate** preventing automatic execution of dangerous commands (`sudo`, `rm -rf`, `mkfs`, `dd`, `chmod -R 777`, `killall`, package installations) without explicit approval tokens.

#### 3.5 Browser & YouTube Controller (`tools/desktop/browser_controller.py`)
- Launches Google Chrome or Firefox with requested URLs.
- Executes YouTube searches: formats URL `https://www.youtube.com/results?search_query=...`, launches browser, verifies window creation, and truthfully reports search page status (distinguishing browser page display from physical audio playback).

#### 3.6 Desktop Window Manager (`tools/desktop/window_manager.py`)
- Queries active window title, ID, class name, and PID via `xdotool`.
- Lists open top-level windows via `wmctrl -l -p -G`.
- Queries screen dimensions via `xdpyinfo` (1360x768 native resolution on Raspberry Pi 5).

### 4. Integration with AI Agent & Chat API
- Synchronous and SSE chat endpoints automatically intercept Phase 2 intents (`desktop_open_app`, `desktop_open_url`, `desktop_search_youtube`, `desktop_open_project`, `desktop_search_files`, `desktop_search_content`, `desktop_run_program`, `terminal_execute`, `desktop_awareness`).
- Multi-step requests (e.g. Test 10) are handled by `CompoundTaskOrchestrator`, which decomposes the request into ordered operations and returns a consolidated markdown report.
