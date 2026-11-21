# Security & Data Privacy — Module 28: AI Data Analyst

- **Local-First Computation**: All CSV/JSON parsing, statistical profiling, Z-score anomaly detection, and group-by aggregations execute locally in Python with no outbound data transfer.
- **No Arbitrary Code Execution (`eval`/`exec`)**: Natural-language questions are answered via deterministic structured operations rather than executing untrusted generated Python/SQL code.
- **Payload & Input Bounds**: CSV uploads are capped by Pydantic validation (`max_length=500000`), and all SQLite queries use parameterized `?` bindings.
- **Simulation Disclosure**: `LocalDataInsightAdapter` reports `simulated: true` on `/health`, `/status`, and Q&A responses.
- **No Hardcoded Secrets**: Verified via static secret scan across all files.
