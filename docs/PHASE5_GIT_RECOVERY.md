# JARVIS OS — Phase 5 Git Recovery & Safety Specification
## Atomic Snapshots, Pre-Repair State Tracking, Syntax Gates & Rollback

---

# 1. Overview & Rollback Guarantee

Automated code repair can introduce syntax errors, regression bugs, or corrupted files if left unconstrained. The **Git Safety Manager** (`tools/agents/git_safety.py`) guarantees that **no change is ever committed without explicit validation**, and **any broken change is automatically rolled back in milliseconds**.

---

# 2. Snapshot Lifecycle

### 2.1 Snapshot Creation
Before any agent is granted write permission to project files:
1. `GitSafetyManager.create_pre_repair_checkpoint(task_id, target_files, workspace_dir)` executes.
2. Captures Git HEAD commit hash (`git rev-parse HEAD`).
3. Captures uncommitted file modifications (`git status --porcelain`).
4. Creates a snapshot directory: `data/agents/snapshots/ckpt_<task_id>_<timestamp>/`.
5. Copies original versions of all target files into the snapshot directory.

### 2.2 Pre-Test Syntax Validation Gate
Before running test suites, `git_safety.validate_syntax(filepath)` compiles the modified Python file using `py_compile.compile(..., doraise=True)`.
- If an AST syntax error is detected (e.g., unterminated string literal, invalid syntax, indentation mismatch), execution is halted immediately.
- The pipeline bypasses test execution and rolls back directly, preventing confusing test runner crashes.

### 2.3 Rollback Execution
If tests fail or an error occurs:
1. `GitSafetyManager.rollback(task_id)` iterates through all backed-up files.
2. Overwrites modified workspace files with their pristine snapshot copies.
3. Restores original file timestamps.
4. Returns `{status: "ok", restored_files: [...]}` in <50ms.

### 2.4 Cleanup
Upon verified repair success (`RUNTIME_VERIFIED`):
`GitSafetyManager.cleanup_checkpoint(task_id)` deletes the temporary snapshot directory to prevent disk bloat.
