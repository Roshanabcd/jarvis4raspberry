# Hybrid JARVIS Developer

Standalone mock-first orchestration foundation. It uses a separate SQLite database (`orchestration.sqlite3` by default); it never opens `jarvis_memory.db`. `discover(root)` returns paths only. Simulated agents operate only on task objects and do not touch files or hardware.

## Isolated parallel development (Phase 04)

`WorktreeManager` creates a dedicated `hybrid/<task-id>` branch and Git worktree per task under a caller-selected root. It refuses to reuse an existing worktree path, records a working-tree status checkpoint, and returns review metadata only after a caller-supplied test gate passes. It never merges. A human must review and merge proposals. Keep the worktree root outside the stable checkout. `detect_conflicts` detects overlapping path ownership, including parent/child overlaps; callers must serialize tasks with intersecting claims. Dependencies remain enforced by task scheduling. Use `max_concurrency` to bound jobs. OS resource limits are not imposed by the portable core; run agents inside externally managed resource controls when available. A restart can reopen stored task metadata and retained branch/worktree; inspect `git status` before resuming, and never discard uncommitted edits.

## Use

Add this directory to `PYTHONPATH` and import `core`, `models`, and `simulated` (hyphens prevent ordinary package import syntax). Register an `Agent` with named `Capability` entries, create tasks, then call `run(task_id)` after dependencies have succeeded. Database location and concurrency are configurable in `Orchestrator`.

## Eventual JARVIS connection

Integrate later through a narrow application-owned adapter: the main JARVIS application may submit validated typed tasks and consume results through an explicit API boundary. Keep memory storage separate, preserve a single owner for hardware, and require authorization for any future write-capable agent. This phase includes no service, API, entry-point, provider, or hardware integration; agents are mocks only. Timeout is enforced for result waiting, though Python cannot forcibly terminate a running thread. Cancellation is persisted for queued tasks; in-flight adapter cancellation requires cooperative adapter support.
