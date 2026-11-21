# Module 35 — Visual Workflow Builder (`v1.0.0`) Test Report

## Execution Summary

- **Module ID**: `jarvis-module-35-visual-workflow-builder`
- **Engine Mode**: `local_dag_workflow_engine` (`simulated: false` — real Kahn topological DAG validator & deterministic local execution engine backed by SQLite WAL)
- **Python Environment**: Python 3.11.2, FastAPI 0.92.0, Pydantic 1.10.4, Starlette 0.26.1, HTTPX 0.23.3

| Suite | Runner | Status | Result | Notes |
|---|---|---|---|---|
| Static Bytecode Check | `python3 -m compileall -q backend examples tests` | **EXECUTED** | **PASS** | 0 syntax/import errors |
| Backend Unit & API Tests (`tests/backend/`) | `python3 -m unittest discover -s tests/backend -v` | **EXECUTED** | **PASS (6/6)** | DAG cycle detection (`422`), invalid edges (`422`), duplicate nodes (`422`), topological execution, conditional branch skipping, `/health`, `/manifest`, `/workflows` HUD, `/graphs`, `/validate`, `/execute`, `/ws/runs` |
| Host Integration Tests (`tests/integration/`) | `python3 -m unittest discover -s tests/integration -v` | **EXECUTED** | **PASS (2/2)** | `mount_module` into host FastAPI app, `app.state.workflows`, end-to-end graph execution & run history |
| Runnable CLI Demo | `python3 examples/run_workflow_demo.py` | **EXECUTED** | **PASS** | Verified high-value alert dispatch & low-value conditional branch skip (`simulated: false`) |
| Static Secret Scan | Regex scan across staged files | **EXECUTED** | **PASS (0 hits)** | No hardcoded keys, tokens, or private keys |
| Frontend Component Tests (`tests/frontend/DashboardPage.test.tsx`) | `vitest` / `tsc` | **NOT EXECUTED** | **NOT EXECUTED** | `vitest` and `tsc` are not installed in this offline sandbox VM; run `npm install && npm test` on target host |
| E2E Browser Tests (`tests/e2e/workflows.spec.ts`) | `playwright` | **NOT EXECUTED** | **NOT EXECUTED** | `playwright` is not installed in this offline sandbox VM; run `npx playwright test` against port `8135` on target host |
| Clean-Room ZIP Archive Verification | `zipfile.testzip()` + fresh temp extract + `unittest` + CLI demo | **EXECUTED** | **PASS (8/8)** | Verified zero corrupt entries and full pass after clean-room extraction |
