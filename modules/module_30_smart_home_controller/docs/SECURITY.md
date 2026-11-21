# Security & Safety Model — JARVIS Module 30 (Smart Home Controller)

## 1. Safety-Gated Physical Access Controls
- **Explicit Unlock Confirmation**: Issuing `command: "unlock"` on any `lock` device without `confirm_unlock: true` is deterministically blocked with HTTP `409 Conflict` (`UNLOCK_CONFIRMATION_REQUIRED`).
- **Scene & Rule Restrictions**: `SceneActionItem` and `RuleCreateRequest` schemas intentionally omit `unlock` from allowed automated commands so unattended scenes or sensor rules cannot silently unlock doors.

## 2. Persistence & Auditability
- All device registrations, state mutations, blocked unlock attempts, scene activations, and rule triggers are recorded in SQLite WAL (`device_events`) with UTC ISO-8601 timestamps.
- Parameterized SQL queries are used throughout `SmartHomeDB` to prevent SQL injection.

## 3. Simulation Transparency
- Every `/health` and `/status` response explicitly reports `simulated: true` when using `SimulatedSmartHomeBridgeAdapter`, ensuring operators and upstream JARVIS orchestrators never mistake simulated device states for real physical actuators.

## 4. Production Hardening Recommendations
- Place Module 30 behind the JARVIS OS reverse proxy or LAN firewall; restrict `JARVIS_M30_CORS_ORIGINS` to trusted origins.
- Store Home Assistant / MQTT broker credentials in `.env` (never committed to git) when implementing a custom `SmartHomeBridgeAdapter`.
