# JARVIS OS — Phase 2 Terminal Execution Guide
## Production Guide to the Real Terminal Execution Subsystem

### 1. Overview
The JARVIS Terminal Execution Subsystem (`tools/terminal/terminal_manager.py`) allows JARVIS to execute real Linux shell commands natively on the Raspberry Pi 5 without simulation, artificial sandboxing, or mocked output.

### 2. Key Capabilities
1. **Real Standard Output & Error Capture:** Output from stdout and stderr is captured verbatim and returned with execution duration and exit codes.
2. **Persistent Directory Tracking (CWD):** Each session maintains its own working directory state. Calling `cd <path>` persists across subsequent commands within that session.
3. **Session Management:** Independent sessions (e.g. `default`, `build_session`, `test_session`) maintain isolated directory contexts and command histories.
4. **Interactive Support:** Commands with pipes (`|`), redirects (`>`, `>>`), and environment variables execute via `/bin/bash -c`.
5. **Background Process Tracking:** Long-running processes are tracked with unique `job_id`, PID, log file path, and can be stopped via API.

### 3. Security Confirmation Gate
To protect the system against accidental destructive actions, the engine intercepts sensitive patterns before execution:
- Superuser privileges: `sudo`
- Destructive file deletion: `rm -rf`, `rm -fr`, `rmdir`
- Filesystem/disk manipulation: `mkfs`, `fdisk`, `parted`, `dd if=`
- Recursive permission changes: `chmod -R`, `chown -R`
- Package manager modifications: `apt install`, `apt-get`, `dpkg`
- Systemd service disruption: `systemctl stop`, `systemctl disable`
- Network configuration: `iptables`, `ufw`
- Process killing: `kill -9`, `killall`, `pkill`
- Remote script piping: `curl ... | bash`

#### Confirmation Protocol
When a dangerous command is submitted without `confirm=True`:
1. The command is halted immediately.
2. A unique confirmation token is generated (e.g. `tok_88cca10c0434`).
3. Status `CONFIRMATION_REQUIRED` is returned with an explanatory reason.
4. The user or frontend must explicitly confirm execution by passing `confirm=True` and `confirmation_token="<token>"`.

### 4. REST API Reference

#### Execute Command
`POST /api/terminal/execute`
```json
{
  "command": "python3 --version",
  "session_id": "default",
  "confirm": false,
  "confirmation_token": null,
  "timeout": 45
}
```
**Response:**
```json
{
  "command": "python3 --version",
  "cwd": "/home/roshan",
  "exit_code": 0,
  "stdout": "Python 3.14.6\n",
  "stderr": "",
  "duration_ms": 5,
  "status": "SUCCESS"
}
```

#### List Sessions
`GET /api/terminal/sessions`

#### Get Command History
`GET /api/terminal/history?session_id=default`

#### Process Management
- List running jobs: `GET /api/terminal/processes`
- Stop a job: `POST /api/terminal/processes/{job_id}/stop`
