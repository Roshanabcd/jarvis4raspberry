# JARVIS OS — Module 40: Permissions & Approval Center (`v1.0.0`)

Fail-closed policy evaluator, human-in-the-loop approval queue with TTL expiration, immutable governance audit log, and interactive HUD for JARVIS OS.

## Key Capabilities
- **Fail-Closed Policy Engine (`simulated: false`)**: Evaluates `(module_id, action)` requests against persisted SQLite WAL policies (`auto_allow`, `require_approval`, `auto_deny`), defaulting unknown actions to `require_approval`.
- **Single-Decision Lock & TTL Expiration**: Prevents double-deciding (`409 REQUEST_ALREADY_DECIDED`) and automatically expires stale pending requests (`410 REQUEST_EXPIRED`).
- **Immutable Audit Trail**: Logs every submission, human approval/denial, and TTL expiration into `approval_audit`.
- **Standalone HUD & Host Mount**: Serves `/approvals` directly from FastAPI (`port 8140`) and mounts cleanly into JARVIS OS via `backend.app.main:mount_module`.

## Quick Start
```bash
./scripts/setup.sh
./scripts/run.sh
# Open http://localhost:8140/approvals
```
