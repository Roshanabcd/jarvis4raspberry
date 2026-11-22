# JARVIS OS — Module 22: Intelligent AI Model Router (`v1.0.0`)

Task-aware multi-model AI routing engine for **JARVIS OS**, providing explainable candidate scoring, automatic failover with circuit breakers, daily USD budget guardrails with automatic local-model downgrade, deterministic SHA-256 response caching, side-by-side model benchmarking, SQLite WAL persistence, and a futuristic JARVIS-themed control UI.

> **Simulation Transparency**: By default, Module 22 runs with `SimulatedModelProviderAdapter` (`simulated: true`) so you can test routing strategies, circuit-breaker failovers, budget guardrails, and caching locally with zero external API keys or network calls. Subclass `ModelProviderAdapter` to connect live Ollama, Gemini, OpenAI, or Anthropic endpoints.

## Key Capabilities
- **Model & Provider Registry**: Pre-seeded with 6 reference models (`local-llama3-8b`, `local-qwen25-coder`, `gemini-2.5-flash`, `gemini-2.5-pro`, `gpt-4o-mini`, `claude-3-7-sonnet`) and dynamic registration/toggling via REST API.
- **Automatic Task Classification**: Classifies prompts into `coding`, `reasoning`, `summarization`, `vision`, or `general` when `task_type="auto"`.
- **5 Routing Strategies**: `balanced`, `cost_optimized`, `latency_optimized`, `quality_first`, and `local_only` (privacy-first).
- **Failover & Circuit Breaker**: Automatically falls back to the next highest-ranked healthy candidate on failure and opens the circuit breaker after consecutive failures.
- **Budget Guardrails & Caching**: Tracks cumulative spend in SQLite WAL, automatically downgrades to `$0` local models when the daily cap is reached, and caches identical requests via SHA-256 keys.
- **Side-by-Side Benchmarking**: Compares multiple models on the same prompt for latency, token usage, and estimated cost.

## Quick Start
```bash
bash scripts/setup.sh
bash scripts/run.sh
# Open http://127.0.0.1:8122/model-router
```

## Run Automated Tests & Demo
```bash
bash scripts/test.sh
python3 examples/run_router_demo.py
```

## Documentation
- [API Reference](docs/API.md)
- [JARVIS OS Integration Guide](docs/INTEGRATION.md)
- [Security & Privacy Governance](docs/SECURITY.md)
- [Test Verification Report](docs/TEST_REPORT.md)
