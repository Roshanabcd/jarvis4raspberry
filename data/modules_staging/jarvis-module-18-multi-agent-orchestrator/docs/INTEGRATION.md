# Integration Guide — JARVIS OS Module 18 (`v1.0.0`)

## Additive FastAPI Integration (2 Lines)
Copy `jarvis-module-18-multi-agent-orchestrator` onto your Python path (or inside your JARVIS OS repository) and mount it additively without modifying existing JARVIS routes or databases:

```python
from backend.app.main import mount_module

orchestrator = mount_module(app, include_root_ui=False)
# Start/stop inside your existing FastAPI lifespan:
# await orchestrator.start()
# await orchestrator.stop()
```

This exposes:
- UI: `GET /orchestrator`
- REST & WebSocket API: `/api/v1/orchestrator/*`
- Health & Manifest: `/api/v1/orchestrator/health`, `/api/v1/orchestrator/manifest`

## Binding Live JARVIS Core Adapters (Future Modules 19–41)
Module 18 defines versioned abstract contracts in `backend/adapters/contracts.py` (`CONTRACT_VERSION = "1.0.0"`):
- `JarvisCoreAdapter`
- `JarvisOrchestratorContract`
- `JarvisEventBusAdapter`
- `JarvisApprovalAdapter` (future Module 40: Permissions & Approval Center)
- `JarvisModelProviderAdapter` (future Module 22: Intelligent AI Model Router)
- `JarvisLoggingAdapter`, `JarvisConfigAdapter`, `JarvisStorageAdapter`

Pass a custom `StandaloneHarness` (or live adapter bundle) into `MultiAgentOrchestrator(harness=...)` when binding to JARVIS Core.

## Registering Custom Agents from Other Modules
```python
async def my_robot_handler(task, context):
    return {"status": "ok", "upstream": context["dependency_results"]}

orchestrator.register_handler("robot_brain", my_robot_handler)
```
