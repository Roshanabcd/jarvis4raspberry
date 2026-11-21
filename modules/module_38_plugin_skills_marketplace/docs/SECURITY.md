# Module 38 — Security & Integrity Notes

- **Zero Arbitrary Code Execution**: Publishing or installing a package records verified metadata and SHA-256 checksums without executing untrusted plugin code automatically.
- **Checksum Verification**: Supplying `expected_sha256` during installation enforces digest matching (`422 CHECKSUM_MISMATCH` on tampering).
- **Permission Allowlist**: Only explicitly approved scopes (`read_files`, `write_files`, `network_read`, `calendar_read`, `notifications`, `workflows`, `telemetry_read`) are accepted.
- **Audit Trail**: Every publish, install, toggle, and uninstall operation is appended to `marketplace_audit`.
