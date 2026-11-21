# Module 40 — Security & Governance Notes

- **Fail-Closed Default**: Any `(module_id, action)` without an explicit `auto_allow` policy defaults to `require_approval`.
- **Single-Decision Immutability**: Once approved, denied, or expired, a request cannot be modified (`409 REQUEST_ALREADY_DECIDED`).
- **TTL Enforcement**: Pending requests past `expires_at_epoch` transition to `expired` and return `410 REQUEST_EXPIRED`.
- **Audit Integrity**: Every submission, decision, and expiration is appended to `approval_audit` with actor identity and timestamp.
