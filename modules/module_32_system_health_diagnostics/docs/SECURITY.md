# Security Model — JARVIS Module 32 (System Health & Diagnostics)

1. **SSRF Prevention on Service Probes**: `register_service()` strictly restricts TCP probes to loopback hosts (`127.0.0.1`, `localhost`, `::1`) and rejects external/LAN hosts with `403 HOST_NOT_ALLOWED`.
2. **Read-Only Host Telemetry**: Metrics are gathered from standard POSIX APIs (`os.getloadavg`, `shutil.disk_usage`) and read-only `/proc` / `/sys` files without root privileges or shell command execution.
3. **Parameterized SQLite Queries**: All database reads/writes use bound parameters.
