# Security & Sandboxing — Module 29: Advanced File Manager

- **Strict Sandbox Jail (Path-Traversal Prevention)**: Every file path is canonicalized via `Path.resolve()` and checked against `self.root` (`candidate == self.root or self.root in candidate.parents`). Any `../` escape attempt is rejected with `403 PATH_TRAVERSAL_BLOCKED`.
- **Soft-Delete Recovery**: `DELETE /files` moves files into `_trash/` rather than permanently unlinking them, preserving recovery and auditability.
- **Dry-Run Auto-Organization**: `POST /organize` defaults to `dry_run=True` so operators inspect planned moves before modifying directory layout.
- **Audit Trail & Parameterized SQL**: All mutations are recorded in SQLite WAL `audit_logs` using parameterized queries.
- **No Hardcoded Secrets**: Verified via static secret scan across all files.
