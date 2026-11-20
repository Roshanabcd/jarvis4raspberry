# JARVIS OS — Feature #1: AI Coding Assistant

Strictly additive, Raspberry Pi 5-friendly Developer Tools module for **JARVIS OS**:
- **Intelligent Code Generation** (OpenRouter `openrouter/free`, Local Ollama, or deterministic offline scaffold + manual prompt export)
- **Refactoring & Unified Diff Preview** with safe `dry_run=True` default and timestamped `.bak` backups
- **Security & Quality Static Analysis** (100% local Python AST + multi-language regex scanner for hardcoded secrets, `eval`/`exec`, `os.system`, `subprocess(shell=True)`, `yaml.load`, SQL injection, cyclomatic complexity, and mutable defaults)
- **Automated Test Synthesis** (LLM + deterministic AST `pytest` unit test generator)
- **SQLite (WAL Mode) History & Audit Log**
- **JARVIS OS Dark Cyber Web UI** at `/coding-assistant`

## Quick Start (Standalone on Raspberry Pi 5)

```bash
cd ~/.gemini/antigravity/scratch/jarvis-os
unzip /path/to/jarvis_ai_coding_assistant.zip -d features/
cd features

# Optional: configure your OpenRouter key (uses openrouter/free by default)
export OPENROUTER_API_KEY="your-openrouter-key"
export JARVIS_CODE_WORKSPACE="$HOME/.gemini/antigravity/scratch/jarvis-os"

uvicorn jarvis_ai_coding_assistant.app:app --host 127.0.0.1 --port 8011
```

Open `http://127.0.0.1:8011/coding-assistant` in Chromium on your Raspberry Pi 5.

## Run Tests

```bash
python3 -m unittest discover -s jarvis_ai_coding_assistant/tests -v
# or with pytest:
pytest jarvis_ai_coding_assistant/tests -v
```
