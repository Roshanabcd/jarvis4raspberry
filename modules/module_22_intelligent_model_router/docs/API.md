# API Reference — Module 22: Intelligent AI Model Router

Base prefix: `/api/v1/model-router`  
UI route: `/model-router`  
Contract version: `1.0.0`

## System, Registry & Policy Endpoints
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/model-router/health` | Module health, version, contract version, and simulation flag |
| `GET` | `/api/v1/model-router/manifest` | Returns `manifest.json` |
| `GET` | `/api/v1/model-router/status` | Healthy model count, cumulative spend, cache/failover totals, budget policy |
| `GET` | `/api/v1/model-router/models` | List all registered AI models with circuit breaker & outage state |
| `POST` | `/api/v1/model-router/models` | Register or update a model entry |
| `PATCH` | `/api/v1/model-router/models/{model_id}` | Enable/disable a model, toggle `simulate_outage`, or `reset_circuit` |
| `PUT` | `/api/v1/model-router/budget` | Update `daily_budget_usd`, `downgrade_to_local_on_cap`, or `enable_cache` |
| `POST` | `/api/v1/model-router/cache/clear` | Purge cached responses |

## Routing, Benchmarking, Telemetry & WebSocket
| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/model-router/route` | Classify, score, route, cache, and execute a prompt with automatic failover |
| `POST` | `/api/v1/model-router/benchmark` | Run a prompt side-by-side across up to 6 selected models |
| `GET` | `/api/v1/model-router/logs` | Retrieve persisted routing decision and spend audit logs |
| `WS` | `/api/v1/model-router/ws/events` | Real-time status & heartbeat WebSocket stream |
