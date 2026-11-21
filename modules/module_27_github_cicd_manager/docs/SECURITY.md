# Security & Governance — Module 27: GitHub & CI/CD Manager

- **Constant-Time Webhook Verification**: `verify_webhook_signature()` validates `X-Hub-Signature-256` using `hmac.compare_digest` against `JARVIS_M27_WEBHOOK_SECRET`, rejecting forged or missing signatures with `401`.
- **Mandatory CI Merge & Release Gates**: Repositories with `require_ci_green=True` (default) reject PR merges (`409 CI_GATE_BLOCKED`) and release publishing (`409 RELEASE_BLOCKED`) until CI passes.
- **Simulation Transparency**: `SimulatedGitHubCICDAdapter` sets `simulated: true` on `/health`, `/status`, and every persisted pipeline run.
- **Parameterized SQL & Input Validation**: All database queries use bind parameters and Pydantic schemas enforce valid repo/branch/strategy fields.
- **No Hardcoded Tokens**: Zero GitHub PATs or private keys in source code; set `JARVIS_M27_WEBHOOK_SECRET` via `.env` in production.
