# JARVIS OS — Module 23: Personal Executive Assistant (`v1.0.0`)

Executive productivity module for **JARVIS OS**, providing real local SQLite WAL persistence for goals/OKRs, Eisenhower priority tasks, overlap-checked daily time blocking, a smart day auto-planner, habit streak tracking, delegation follow-ups with overdue alerts, and an automated Daily Executive Briefing.

> **Synthesis Adapter Transparency**: All goals, tasks, time blocks, habit streaks, and follow-ups are stored and computed locally in SQLite WAL. The prose executive summary defaults to `LocalRuleExecutiveAdapter` (`simulated: true`) so it operates completely offline; swap in a live LLM adapter (or route via Module 22) for generative prose briefings.

## Quick Start
```bash
bash scripts/setup.sh
bash scripts/run.sh
# Open http://127.0.0.1:8123/executive-assistant
```

## Run Automated Tests & Demo
```bash
bash scripts/test.sh
python3 examples/run_executive_demo.py
```

## Documentation
- [API Reference](docs/API.md)
- [JARVIS OS Integration Guide](docs/INTEGRATION.md)
- [Security & Privacy](docs/SECURITY.md)
- [Test Verification Report](docs/TEST_REPORT.md)
