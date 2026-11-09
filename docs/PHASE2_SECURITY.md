# JARVIS OS — Phase 2 Desktop & Terminal Security Architecture

## 1. Principles of Desktop Security

1. **Local Isolation:** Terminal execution and desktop actions operate strictly on local system boundaries. No terminal commands, paths, or source file contents are leaked to external AI services.
2. **Non-Root Execution:** All GUI applications, terminal processes, and scripts run strictly under the unprivileged user account (`roshan`, UID 1000). JARVIS rejects executing GUI software as `root`.
3. **Session Authentication:** GUI applications require the logged-in user's X11 credentials (`DISPLAY=:0`, `XAUTHORITY=/home/roshan/.Xauthority`).
4. **Path Traversal Protection:** Filesystem search and file write operations validate target paths to prevent unauthorized directory traversal.

## 2. Security Confirmation Gate

Potentially destructive or system-altering terminal commands cannot execute automatically, even if generated or requested via natural language:

```
[User Request] ──> [Command Parse] ──> [Pattern Check]
                                            |
                      +---------------------+---------------------+
                      | Safe Command                              | Dangerous Command
                      v                                           v
             [Execute in Terminal]                   [Halt Execution & Generate Token]
                      |                                           |
                      v                                           v
             [Return Real Result]                    [Prompt Explicit Approval (UI/API)]
                                                                  |
                                                                  v
                                                     [Confirm=True + Token Match]
                                                                  |
                                                                  v
                                                         [Execute Safely]
```

### Monitored Dangerous Patterns
* Privileged escalation (`sudo`)
* Destructive deletion (`rm -rf`, `rm -fr`, `rmdir`)
* Storage device and filesystem commands (`mkfs`, `fdisk`, `parted`, `dd if=`)
* Recursive permission modifications (`chmod -R`, `chown -R`)
* System package installation (`apt install`, `apt-get`, `dpkg`)
* Service management disruption (`systemctl stop`, `systemctl disable`)
* Network & firewall alterations (`iptables`, `ufw`)
* Untrusted execution pipelines (`curl ... | bash`, `wget ... | sh`)
* Uncontrolled process termination (`kill -9`, `killall`, `pkill`)

## 3. Tool Risk Classification

All desktop and terminal tools registered in `tools/registry.py` are mapped to explicit risk tiers:

* **Level 0 (Read-Only / Informational):** `desktop_get_status`, `desktop_get_active_window`, `desktop_search_files`, `desktop_search_content`, `desktop_open_url`, `desktop_search_youtube`.
* **Level 1 (Standard Desktop Action):** `desktop_open_app`, `desktop_open_project`, `desktop_switch_app`.
* **Level 2 (Privileged / Execution):** `desktop_run_program`, `terminal_execute` (guarded by confirmation gate).
* **Level 3 (Hardware / System Configuration):** Actuator motion, firmware updates.
