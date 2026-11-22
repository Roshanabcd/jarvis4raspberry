# API Reference — JARVIS Module 35: Visual Workflow Builder (`v1.0.0`)

**Base URL:** `http://127.0.0.1:8135/api/v1/workflows`  
**WebSocket:** `ws://127.0.0.1:8135/api/v1/workflows/ws/runs`

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Module health check (`simulated: false`) |
| `GET` | `/manifest` | Returns `manifest.json` |
| `GET` | `/status` | Workflows count, runs count, uptime |
| `GET` | `/graphs` | List saved visual workflow graphs |
| `POST` | `/graphs` | Create & DAG-validate a new workflow graph |
| `POST` | `/graphs/{workflow_id}/validate` | Re-validate DAG structure and return topological `execution_order` |
| `POST` | `/graphs/{workflow_id}/execute` | Execute a workflow with `input_data` and return full per-node trace |
| `GET` | `/runs` | List historical workflow runs (optional `?workflow_id=<id>`) |
| `WS` | `/ws/runs` | Real-time connection & heartbeat status stream |
