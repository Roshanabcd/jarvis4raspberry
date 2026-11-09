# JARVIS OS — Phase 5 Self-Healing Engine Specification
## Autonomous Diagnosis, Patch Generation, Verification Gates & Rollback

---

# 1. Self-Healing Architecture & Mission

The **JARVIS Self-Healing Engine** (`tools/agents/self_healing.py`) enables the system to detect software defects, diagnose the underlying root cause, formulate minimal safe code patches, apply them in an isolated workspace, and verify the repair before declaring completion.

```
+-------------------------------------------------------------------------------+
|                       SELF-HEALING EXECUTION LIFECYCLE                        |
+-------------------------------------------------------------------------------+
  [1. Error Trigger] -> Uncaught Exception / Failed Test / Terminal Error Code
         │
         ▼
  [2. Context Packaging] -> ProblemContextPackager structures failure & scrubs secrets
         │
         ▼
  [3. Pre-Repair Snapshot] -> GitSafetyManager creates byte-for-byte file backups
         │
         ▼
  [4. Agent Selection] -> MultiAgentOrchestrator assigns highest scoring ready agent
         │
         ▼
  [5. Patch Application] -> Coding agent inspects file and applies patch
         │
         ▼
  [6. Syntax Gate] -> py_compile checks Python AST validity
         ├── Invalid AST? ──────────────────────────┐
         │                                          │
         ▼ Valid AST                                │
  [7. Verification Gate] -> Executes pytest suite   │ (Failure)
         ├── Tests Failed? ─────────────────────────┼───────┐
         │                                          │       │
         ▼ Tests Passed                             │       │
  [8. Success Gate]                                 ▼       ▼
     • Commit patch to Git                      [9. Rollback Workspace]
     • Log runtime metrics                         • Restore files from backup
     • Mark task RUNTIME_VERIFIED                  • Failover to next agent
```

---

# 2. Pipeline Stages

### Stage 1: Problem Detection
Catches errors from:
- Terminal exit codes (`returncode != 0`).
- Uncaught Python exceptions (`SyntaxError`, `TypeError`, `IndexError`, `ImportError`, `AssertionError`).
- Test suite failures (`pytest` non-zero status).

### Stage 2: Context Packaging (`ProblemContextPackager`)
- Identifies the primary failing file from tracebacks.
- Collects up to 3 relevant project files.
- Automatically excludes sensitive files (`.env`, `credentials.json`, `id_rsa`, `.pem`, `.key`).
- Scrubs API keys, passwords, and tokens using regex substitution.
- Captures the recent Git commit and porcelain diff.

### Stage 3: Git Safety Snapshot (`GitSafetyManager`)
- Records the current Git commit hash.
- Creates backup copies of all target files under `data/agents/snapshots/ckpt_<task_id>_<timestamp>/`.
- Ensures zero user work is lost even if the coding agent produces invalid or destructive code.

### Stage 4: Agent Selection & Mutex Lock
- Selects the best authenticated coding agent (`antigravity` or `codex`).
- Acquires the exclusive write lock so only one agent touches files at a time.
- Watchdog starts monitoring for execution stagnation or loops.

### Stage 5: Patch Execution
- Passes problem context to the assigned agent.
- Agent generates the patch and writes it to disk.

### Stage 6: AST Syntax Gate
- Runs `py_compile` on modified Python files.
- If syntax compilation fails (e.g., unexpected EOF, unmatched parentheses), the pipeline immediately aborts and rolls back, preventing broken code from running tests.

### Stage 7: Test Verification Gate
- Executes the project's test command (e.g., `pytest tests/unit/...`).
- Captures return code, stdout, and stderr.
- Requires exit code 0 for success.

### Stage 8: Rollback Guarantee
- If syntax fails OR tests fail, `GitSafetyManager.rollback(task_id)` restores every modified file from its pre-repair snapshot within <50 milliseconds.
- Orchestrator attempts failover to secondary agent (up to 3 attempts total).
