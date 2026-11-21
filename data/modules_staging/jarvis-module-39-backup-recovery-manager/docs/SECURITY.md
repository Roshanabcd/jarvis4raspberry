# Module 39 — Security & Integrity Notes

- **Sandbox Confinement**: Both backup sources and restore destinations are resolved against `JARVIS_M39_SANDBOX_ROOT`; absolute paths and `..` traversals fail with `403 PATH_OUTSIDE_SANDBOX`.
- **Zip-Slip Protection**: Every archive entry path is resolved and checked against the restore destination directory before writing (`422 ZIP_SLIP_BLOCKED`).
- **Pre-Restore Integrity Gate**: Every restore invokes `verify_snapshot()` first; tampered or missing archives fail closed with `409 SNAPSHOT_CORRUPTED`.
- **Storage Hardening**: Store `JARVIS_M39_ARCHIVE_DIR` on dedicated backup media with restricted permissions (`chmod 700`).
