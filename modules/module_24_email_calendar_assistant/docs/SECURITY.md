# Security & Outbound Approval Policy — Module 24

- **Mandatory Human Send Gate**: `JARVIS_M24_REQUIRE_APPROVAL_SEND=true` by default ensures no outbound email is ever sent automatically without explicit human approval via `/approvals/{id}/decide`.
- **Safe Offline Simulation**: `SimulatedMailCalendarAdapter` never opens SMTP sockets or contacts external mail servers.
- **Conflict Prevention**: Calendar event creation rejects double-bookings with HTTP `409` unless `allow_overlap=true` is explicitly passed.
