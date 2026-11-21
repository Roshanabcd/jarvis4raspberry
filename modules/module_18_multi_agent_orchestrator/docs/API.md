# API Specification — JARVIS Module 18 (`v1.0.0`)

Base URL: `/api/v1/orchestrator`

## Standard Error Format
```json
{
  "error": {
    "code": "DAG_CYCLE",
    "message": "Circular dependency detected in task graph.",
    "details": {},
    "timestamp": "2026-11-20T14:00:00+00:00"
  }
}
```

## Endpoints

### System & Contract
- `GET /api/v1/orchestrator/health` — Module health, contract version, storage check, and engine status.
- `GET /api/v1/orchestrator/manifest` — Returns `manifest.json`.
- `GET /api/v1/orchestrator/status` — Live queue counts, active workers, max concurrency, pending approvals, uptime.
- `POST /api/v1/orchestrator/engine/pause` — Pause task scheduling.
- `POST /api/v1/orchestrator/engine/resume` — Resume task scheduling.
- `PUT /api/v1/orchestrator/engine/limits` — Body: `{"max_concurrency": 4}` (range 1..32).

### Agents
- `GET /api/v1/orchestrator/agents` — List all registered agents and active load.
- `POST /api/v1/orchestrator/agents` — Register an agent (`name`, `role`, `capabilities`, `max_concurrency`, `handler_type`, `simulated`).
- `PATCH /api/v1/orchestrator/agents/{agent_id}` — Update status (`online`/`paused`/`offline`), concurrency, or capabilities.
- `DELETE /api/v1/orchestrator/agents/{agent_id}` — Remove an idle agent (`409` if busy).

### Tasks & DAG
- `GET /api/v1/orchestrator/tasks?workflow_id=&status=&limit=200` — List tasks ordered by priority DESC, created_at ASC.
- `POST /api/v1/orchestrator/tasks` — Create a task (`title`, `workflow_id`, `priority`, `required_capability`, `depends_on`, `max_retries`, `retry_backoff_sec`, `timeout_sec`, `requires_approval`, `approval_prompt`, `payload`).
- `GET /api/v1/orchestrator/tasks/{task_id}` — Fetch single task with result/error.
- `POST /api/v1/orchestrator/tasks/{task_id}/pause` — Pause task execution.
- `POST /api/v1/orchestrator/tasks/{task_id}/resume` — Resume paused task.
- `POST /api/v1/orchestrator/tasks/{task_id}/cancel?cascade=true` — Cancel task (and downstream dependents when `cascade=true`).
- `GET /api/v1/orchestrator/dag?workflow_id=` — Return `{nodes, edges}` for visualization.
- `GET /api/v1/orchestrator/workflows/{workflow_id}/aggregate` — Aggregate completed results, progress %, errors, and workflow messages.
- `POST /api/v1/orchestrator/demo/launch` — Launch the built-in 4-stage parallel demo DAG with an approval checkpoint.

### Human Approvals, Messaging & Logs
- `GET /api/v1/orchestrator/approvals?status=` — List approval checkpoints.
- `POST /api/v1/orchestrator/approvals/{approval_id}/decide` — Body: `{"approved": true, "decided_by": "operator", "comment": ""}`.
- `GET /api/v1/orchestrator/messages?workflow_id=&agent_id=&limit=100` — List inter-agent messages.
- `POST /api/v1/orchestrator/messages` — Send agent-to-agent or broadcast message.
- `GET /api/v1/orchestrator/logs?task_id=&agent_id=&level=&limit=150` — Query persistent execution logs.
- `GET /api/v1/orchestrator/events?limit=50` — Recent in-memory event bus envelopes.
- `WS /api/v1/orchestrator/ws/events` — Real-time JSON event stream with heartbeat.
