# JARVIS OS — Module 38: Plugin & Skills Marketplace (`v1.0.0`)

Local-first plugin and skills registry with SemVer validation, SHA-256 checksum verification, permission allowlisting, install/toggle/uninstall lifecycle, and an interactive HUD for JARVIS OS.

## Key Capabilities
- **Local SemVer Registry (`simulated: false`)**: Persists plugins & skills in SQLite WAL, enforcing `MAJOR.MINOR.PATCH` versioning, slug format validation (`422`), and duplicate `(slug, version)` rejection (`409`).
- **SHA-256 Integrity & Permission Allowlisting**: Computes SHA-256 digests on publish, enforces `expected_sha256` verification on install (`422 CHECKSUM_MISMATCH`), and restricts permissions to an explicit allowlist.
- **Full Lifecycle & Audit Trail**: Supports `install`, `toggle` (enable/disable), and `uninstall` with immutable audit events.
- **Standalone HUD & Host Mount**: Serves `/marketplace` directly from FastAPI (`port 8138`) and mounts cleanly into JARVIS OS via `backend.app.main:mount_module`.

## Quick Start
```bash
./scripts/setup.sh
./scripts/run.sh
# Open http://localhost:8138/marketplace
```
