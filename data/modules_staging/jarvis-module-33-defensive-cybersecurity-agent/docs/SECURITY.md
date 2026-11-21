# Security & Defensive Scope — JARVIS Module 33

1. **Strictly Defensive Posture**: Module 33 never performs network scanning, port exploitation, or automated firewall mutation. It inspects local sandboxed files and operator-supplied logs to surface remediation guidance.
2. **Sandbox Boundary Enforcement**: All filesystem scans and FIM operations resolve paths strictly within `JARVIS_M33_SCAN_ROOT` and reject traversal attempts with `403 PATH_OUTSIDE_SANDBOX`.
3. **Automatic Secret Redaction**: Any credential pattern matched during secret scans is masked (`first4...last4`) before persistence or API response so incident logs never expose plaintext credentials.
