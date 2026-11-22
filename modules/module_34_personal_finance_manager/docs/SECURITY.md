# Security & Privacy Model — JARVIS Module 34 (Personal Finance Manager)

1. **100% Local Persistence**: Financial records remain strictly in your local SQLite WAL file (`JARVIS_M34_DB_PATH`) with zero outbound network transmission.
2. **Input Validation & Parameterized SQL**: All numeric amounts are validated (`gt=0`) via Pydantic schemas and written with parameterized SQL queries.
3. **Production Hardening**: Restrict filesystem permissions on `data/jarvis_finance.db` (`chmod 600`) and run behind authenticated JARVIS OS LAN access.
