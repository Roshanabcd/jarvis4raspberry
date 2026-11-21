# Module 37 — Security & Safety Notes

- **Simulated Bridge Transparency**: Default execution runs in `simulated_mesh_device_bridge` (`simulated: true`) without issuing live SSH, ADB, or LAN packets.
- **Explicit Capability Allowlist**: Only declared capabilities (`clipboard`, `media`, `notifications`, `lock`, `power`, `display`) can be registered or invoked; unsupported capabilities return `422`.
- **Offline Safety Guard**: Commands targeted at offline nodes are rejected with `409 DEVICE_OFFLINE` rather than silently queued.
- **Production Hardening**: When attaching a real transport adapter (e.g., Tailscale + mTLS), require mutual device authentication and restrict `JARVIS_M37_CORS_ORIGINS`.
