# JARVIS OS — Phase 5 System Architecture
## Multi-AI Agent Orchestration, Autonomous Debugging, Permission Management & Self-Healing Engine

---

# 1. Executive Overview

Phase 5 equips JARVIS OS on Raspberry Pi 5 (8 GB RAM) with an enterprise-grade **Autonomous Multi-AI Agent Development Engine**. Rather than relying on a single static AI model or brittle rule set, JARVIS dynamically discovers, evaluates, coordinates, and governs external and local AI coding agents (`agy`, `codex`, `claude`, `opencode`, `ollama`) to autonomously detect, diagnose, repair, and verify software defects within project workspaces.

Every operation is bounded by strict security boundaries, isolated file-level snapshots, and automated rollback guarantees.

---

# 2. System Architecture Diagram

```
                                      ┌────────────────────────────────────────────────┐
                                      │           USER INTERACTION CHANNELS            │
                                      │  Chat SSE / Web Dashboard / USB Voice Mic / API│
                                      └───────────────────────┬────────────────────────┘
                                                              │
                                                              ▼
                                      ┌────────────────────────────────────────────────┐
                                      │             JARVIS OS CORE BRAIN               │
                                      │      (ai/brain.py & ai/local_engine.py)        │
                                      └───────────────────────┬────────────────────────┘
                                                              │
                                           Intent Classification & Routing
                                                              │
                                                              ▼
  ┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │                                    PHASE 5 AGENT ORCHESTRATION SUBSYSTEM                               │
  │                                                                                                        │
  │   ┌───────────────────────────┐    ┌───────────────────────────┐    ┌──────────────────────────────┐   │
  │   │       Agent Registry      │    │    Permission Manager     │    │     Stuck-Task Watchdog      │   │
  │   │ (tools/agents/registry.py)│    │ (permission_manager.py)   │    │  (tools/agents/watchdog.py)  │   │
  │   │  • Truthful Discovery     │    │  • SAFE_AUTO (default)    │    │  • 120s Global Timeout       │   │
  │   │  • Secret-Free Auth Check │    │  • SUPERVISED_AUTO        │    │  • Repeated Command Loop     │   │
  │   │  • Capability Matrix      │    │  • MANUAL                 │    │  • Stagnation Detection      │   │
  │   │  • Status Persistence     │    │  • Hard-Deny Boundaries   │    │  • Safe Process Termination  │   │
  │   └─────────────┬─────────────┘    └─────────────┬─────────────┘    └──────────────┬───────────────┘   │
  │                 │                                │                                 │                   │
  │                 └────────────────────────────────┼─────────────────────────────────┘                   │
  │                                                  │                                                     │
  │                                                  ▼                                                     │
  │                                ┌───────────────────────────────────┐                                   │
  │                                │     Multi-Agent Orchestrator      │                                   │
  │                                │  (tools/agents/orchestrator.py)   │                                   │
  │                                │  • Intelligent Agent Scoring      │                                   │
  │                                │  • Concurrency Mutex (Max 1 Write)│                                   │
  │                                │  • Bounded Failover (Max 2-3)     │                                   │
  │                                │  • Second-Opinion Code Review     │                                   │
  │                                └─────────────────┬─────────────────┘                                   │
  │                                                  │                                                     │
  │                                                  ▼                                                     │
  │                                ┌───────────────────────────────────┐                                   │
  │                                │    Autonomous Self-Healing Engine │                                   │
  │                                │   (tools/agents/self_healing.py)  │                                   │
  │                                │  • Problem Context Packager       │                                   │
  │                                │  • Git Safety & Snapshots         │                                   │
  │                                │  • AST Syntax Validation          │                                   │
  │                                │  • Test Verification Gates        │                                   │
  │                                │  • Automatic Clean Rollback       │                                   │
  │                                └─────────────────┬─────────────────┘                                   │
  └──────────────────────────────────────────────────┼─────────────────────────────────────────────────────┘
                                                     │
                                                     ▼
  ┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │                                   ADAPTER LAYER (tools/agents/adapters)                                │
  │                                                                                                        │
  │  ┌───────────────────────┐ ┌───────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐  │
  │  │  AntigravityAdapter   │ │     CodexAdapter      │ │    ClaudeAdapter     │ │    OllamaAdapter     │  │
  │  │  (Google Antigravity) │ │    (OpenAI Codex)     │ │(Anthropic Claude Code│ │ (Local LLaMA/Qwen)   │  │
  │  │  CLI: agy (v1.5.3)    │ │  CLI: codex (v0.152.1)│ │  CLI: claude (v2.1)  │ │ HTTP: 127.0.0.1:11434│  │
  │  │  STATUS: READY        │ │  STATUS: READY        │ │  STATUS: UNAUTH      │ │ STATUS: READY        │  │
  │  └───────────────────────┘ └───────────────────────┘ └──────────────────────┘ └──────────────────────┘  │
  └────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

# 3. Core Subsystems & Components

## 3.1 Agent Registry (`tools/agents/registry.py`)
- Discovers installed CLI executables via standard PATH inspection (`/home/roshan/.local/bin/`, `/usr/bin/`, `/home/roshan/.npm-global/bin/`).
- Safely probes authentication without storing or exposing API keys, passwords, or bearer tokens.
- Persists discovered agent state in `data/agents/registry.json`.
- Enforces truthful status reporting (`READY`, `UNAUTHENTICATED`, `NOT_INSTALLED`, `BUSY`, `ERROR`).

## 3.2 Permission Governance Engine (`tools/agents/permission_manager.py`)
- Centralized gatekeeper for all agent-initiated filesystem and shell operations.
- Three runtime operational profiles:
  - **`SAFE_AUTO` (Default):** Auto-permits safe reads (`read_file`, `list_dir`) and workspace edits (`file_write` in approved directories). Prompts for external writes and package installations. Hard-denies destructive commands.
  - **`SUPERVISED_AUTO`:** Auto-permits safe reads. Prompts for all file writes, patches, and command executions.
  - **`MANUAL`:** Prompts for every operation regardless of risk.
- **Hard-Deny Boundaries (Bypass-Proof):**
  - Destructive recursive deletion: `rm -rf /`, `rm -rf ~`, `rm -rf *`
  - Raw disk partitioning / formatting: `mkfs`, `fdisk`, `dd if=... of=/dev/...`
  - Unrestricted privilege escalation: `sudo su`, `sudo -i`, `sudo bash`
  - System permission destruction: `chmod 777 /`
  - Microcontroller/firmware flashing: `esptool`, `avrdude`, `flashrom`
  - Physical robot hardware actuation: `robot_move`, `servo_set`
  - Firewall tampering: `iptables -F`, `ufw disable`
  - Unverified script execution from internet: `curl ... | bash`

## 3.3 Stuck-Task Watchdog (`tools/agents/stuck_watchdog.py`)
- Continuous monitoring of long-running agent processes.
- Enforces a 120-second maximum execution timeout per task.
- Detects repeated command loops (e.g., executing the exact same command 3 consecutive times with identical output).
- Detects output stagnation (zero stdout/stderr activity for >60s).
- Implements safe PID termination via `SIGTERM` followed by `SIGKILL` escalation if required.

## 3.4 Git Safety & Rollback Engine (`tools/agents/git_safety.py`)
- Automatically captures pre-repair state before touching any workspace file.
- Records initial Git commit hash, porcelain status, and creates byte-for-byte file snapshots in `data/agents/snapshots/ckpt_<task_id>_<timestamp>/`.
- Pre-verifies modified files using Python AST compilation (`py_compile`) to catch syntax errors before test execution.
- Provides atomic, one-click rollback restoring modified files cleanly if post-repair tests fail.

## 3.5 Multi-Agent Orchestrator (`tools/agents/orchestrator.py`)
- Evaluates incoming task complexity and assigns tasks based on intelligent multi-factor scoring (speed, file editing support, context window, local vs cloud).
- Enforces **Write Concurrency Lock (Mutex):** Only 1 coding agent is permitted write access to project files at any time, preventing conflicting overwrites.
- Implements **Bounded Failover:** Up to 2-3 fallback attempts with alternative agents before marking task failed.
- Coordinates **Second-Opinion Review:** An independent, read-only agent reviews proposed patches without write access.

## 3.6 Self-Healing Engine (`tools/agents/self_healing.py`)
- Coordinates the end-to-end autonomous diagnosis and repair pipeline:
  1. Capture failure context via `ProblemContextPackager` (sanitizing secrets).
  2. Create pre-repair safety snapshot.
  3. Select best available coding agent.
  4. Delegate diagnosis and patch application.
  5. Validate AST syntax (`py_compile`).
  6. Execute verification test command (`pytest`).
  7. If verified: commit and mark `RUNTIME_VERIFIED`.
  8. If failed: rollback workspace to snapshot and failover to secondary agent.
