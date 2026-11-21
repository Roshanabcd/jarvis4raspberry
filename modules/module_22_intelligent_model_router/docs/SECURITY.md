# Security & Privacy Governance — Module 22: Intelligent AI Model Router

## 1. Local-Only Privacy Enforcement
- Passing `strategy="local_only"` or `require_local=True` restricts candidate selection strictly to models with `privacy_tier="local"`, preventing sensitive prompts from leaving the device.
- When `daily_budget_usd` is reached and `downgrade_to_local_on_cap=True`, cloud models are automatically excluded in favor of `$0` local models.

## 2. Secret & Credential Hygiene
- No API keys are hardcoded or persisted in SQLite.
- Live provider adapters should read credentials exclusively from environment variables at runtime.

## 3. Resilience & Auditability
- Circuit breakers automatically isolate failing providers after consecutive failures (`JARVIS_M22_CB_THRESHOLD`).
- Every routing decision, failover attempt, cache hit, token count, and USD cost is logged in `routing_logs`.
