# JARVIS OS — Module 39: Backup & Recovery Manager (`v1.0.0`)

Local-first sandboxed ZIP snapshot backup manager with SHA-256 & CRC integrity verification, Zip-Slip-protected restoration, SQLite WAL catalog, and an interactive HUD for JARVIS OS.

## Key Capabilities
- **Real Local ZIP Snapshots (`simulated: false`)**: Archives files inside `JARVIS_M39_SANDBOX_ROOT` into real `.zip` snapshots under `JARVIS_M39_ARCHIVE_DIR`, recording file count, byte size, and SHA-256 digest in SQLite WAL.
- **Tamper & Corruption Detection**: Verifies both on-disk SHA-256 and `zipfile.testzip()` CRC integrity before any restore (`409 SNAPSHOT_CORRUPTED` if altered or missing).
- **Path-Traversal & Zip-Slip Protection**: Blocks `..` escapes and absolute paths (`403 PATH_OUTSIDE_SANDBOX`) plus unsafe ZIP member paths (`422 ZIP_SLIP_BLOCKED`).
- **Standalone HUD & Host Mount**: Serves `/backups` directly from FastAPI (`port 8139`) and mounts cleanly into JARVIS OS via `backend.app.main:mount_module`.

## Quick Start
```bash
./scripts/setup.sh
./scripts/run.sh
# Open http://localhost:8139/backups
```
