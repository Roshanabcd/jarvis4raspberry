# JARVIS OS — Module 18: Multi-Agent Task Orchestrator (`v1.0.0`)

Unified, integration-ready multi-agent execution engine for **JARVIS OS** (Phase A — Core AI Operating System). Built to run completely standalone today and mount cleanly into an existing JARVIS OS FastAPI backend later via the versioned **JARVIS Common Module Contract (`v1.0.0`)**.

## Key Features
- **Agent Registry & Capability Routing**: Register, update, pause, and remove agents with per-agent concurrency caps and least-loaded selection.
- **DAG Dependency Scheduling & Cycle Protection**: Declare `depends_on` relationships; circular or missing dependencies are rejected with structured `422` errors.
- **Priority Queue & Bounded Parallelism**: Schedules `CRITICAL (4) > HIGH (3) > NORMAL (2) > LOW (1)` tasks concurrently up to configurable global and per-agent limits.
- **Persistent SQLite WAL Queue**: Survives restarts and automatically recovers interrupted `running` tasks back to `queued`.
- **Pause, Resume & Cancel Controls**: Pause/resume the entire scheduler or individual tasks; cancel tasks with optional downstream dependency cascade.
- **Retry with Exponential Backoff & Strict Timeouts**: Enforced via `asyncio.wait_for`.
- **Human Approval Checkpoints**: Tasks flagged `requires_approval=true` pause in `awaiting_approval` until an operator approves or rejects them.
- **Inter-Agent Message Bus & Workflow Result Aggregation**: Structured agent-to-agent or broadcast messaging plus `/workflows/{workflow_id}/aggregate`.
- **Futuristic JARVIS Control Dashboard**: Full React + TypeScript + Vite + Tailwind + Framer Motion + Recharts frontend (`frontend/`), plus an instant zero-build standalone UI served directly by FastAPI at `/` and `/orchestrator`.

## Quick Start (Standalone)
```bash
# 1. Backend + Instant Standalone UI (no Node build required)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port 8118
# Open http://localhost:8118/orchestrator

# 2. Optional React + Vite Dev Server
cd frontend && npm install && npm run dev
# Open http://localhost:5118
```

## Simulation Mode Disclosure
By default, Module 18 runs with local reference agents (`ARIA Research Synth`, `AEGIS Gated Executor`) clearly marked as **SIMULATED** alongside real local static-analysis and DAG-aggregation agents (`ATLAS Static Auditor`, `NEXUS Result Aggregator`). No external cloud APIs, credentials, or host hardware are accessed.

## Documentation
- `docs/API.md` — Complete REST & WebSocket API reference
- `docs/INTEGRATION.md` — 2-line additive JARVIS OS integration & adapter contracts
- `docs/SECURITY.md` — Security boundaries, approval gates, and limitations
- `docs/TEST_REPORT.md` — Executed & non-executed test results
