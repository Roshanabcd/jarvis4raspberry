# JARVIS OS — Module 21: Intelligent Browser Agent (`v1.0.0`)

Policy-governed browser automation module for **JARVIS OS**, featuring real HTML DOM extraction, Pillow-based screenshot capture & analysis, SSRF/private-IP protection, domain allowlist/denylist policies, human approval checkpoints for form submissions, sandboxed download management with SHA-256 verification, multi-page workflow orchestration with cancellation, SQLite WAL persistence, and a futuristic JARVIS-themed control UI.

> **Simulation Transparency**: By default, Module 21 runs with `SafeSimulatedBrowserAdapter` against local `*.jarvis.local` HTML fixtures so it never makes unsolicited outbound network requests or alters external websites. Implement `BrowserAutomationAdapter` (e.g., Playwright/Chromium) to connect a live browser when explicitly authorized.

## Key Capabilities
- **Browser Session Management**: Create, track, navigate, inspect, and close isolated browser sessions persisted in SQLite WAL.
- **Site Permission & SSRF Policy Engine**: Enforces `http`/`https` schemes, blocks localhost/loopback/private/link-local/reserved IPs, and checks configurable domain allowlists and denylists.
- **Real HTML DOM Extraction**: Standard-library `HTMLParser` (`DOMExtractorParser`) extracts page titles, headings (`h1`–`h3`), links, forms, input fields, and text previews.
- **Screenshot Capture & Analysis**: Generates ASCII-safe Pillow PNG viewports with mean brightness, dimensions, and detected DOM element summaries.
- **Human Approval Gates for Form Submissions**: Form fills are staged safely; form submissions pause in `awaiting_approval` until an operator approves or rejects them.
- **Multi-Page Workflows & Cancellation**: Execute chained navigation, inspection, form submission, and download steps with pause/resume on approval and explicit task cancellation.
- **Sandboxed Download Manager**: Downloads files into a dedicated sandbox directory with filename sanitization and SHA-256 digests.
- **Dual UI**: Zero-build standalone FastAPI-served JARVIS UI (`/browser-agent`) plus a modular React/TypeScript/Vite/Tailwind frontend (`frontend/`).

## Quick Start
```bash
bash scripts/setup.sh
bash scripts/run.sh
# Open http://127.0.0.1:8021/browser-agent
```

## Run Automated Tests & Demo
```bash
bash scripts/test.sh
python3 examples/run_browser_demo.py
```

## Documentation
- [API Reference](docs/API.md)
- [JARVIS OS Integration Guide](docs/INTEGRATION.md)
- [Security & SSRF Policy](docs/SECURITY.md)
- [Test Verification Report](docs/TEST_REPORT.md)
