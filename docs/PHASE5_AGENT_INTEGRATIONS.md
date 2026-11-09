# JARVIS OS — Phase 5 Agent Integrations Guide
## Adapter Specifications, CLI Command Structures & Execution Protocols

---

# 1. Overview

JARVIS OS uses a standardized adapter architecture (`tools/agents/adapters/base.py`) providing a unified abstraction across heterogeneous AI coding agents. Every adapter encapsulates:
1. Discovery and authentication verification.
2. Safe CLI / API execution.
3. Process lifecycle management and PID tracking.
4. Cancellation via POSIX process signals.
5. Standardized response formatting.

---

# 2. Agent Integration Details

## 2.1 Google Antigravity Adapter (`tools/agents/adapters/antigravity_adapter.py`)
- **Binary:** `agy` (`/home/roshan/.local/bin/agy`)
- **Execution Mode:** Non-interactive headless execution using the prompt flag `-p`.
- **Command Template:**
  ```bash
  agy -p "<sanitized_prompt>" --add-dir "<workspace_dir>" --output-format json
  ```
- **Capabilities:**
  - Full codebase indexing and multi-file analysis.
  - Generates unified diffs and direct file patches.
  - Default Model: `gemini-3.8-flash-high` (high speed, 1M context token window).
  - Alternative Models: `gemini-3.8-flash-medium`, `claude-sonnet-4-6`, `gpt-oss-120b-medium`.

## 2.2 OpenAI Codex Adapter (`tools/agents/adapters/codex_adapter.py`)
- **Binary:** `codex` (`/home/roshan/.local/bin/codex`)
- **Execution Mode:** Non-interactive batch execution via `codex exec`.
- **Command Template:**
  ```bash
  codex exec "<sanitized_instruction>" --dir "<workspace_dir>" --sandbox
  ```
- **Code Review Protocol:**
  ```bash
  codex review --diff "<git_diff>"
  ```
- **Capabilities:**
  - Fast single-file and multi-file code editing.
  - AST-aware Python code generation.
  - Default Model: `gpt-4o`.
  - Alternative Models: `o3-mini`, `codex-default`.

## 2.3 Anthropic Claude Code Adapter (`tools/agents/adapters/claude_adapter.py`)
- **Binary:** `claude` (`/home/roshan/.local/bin/claude`)
- **Execution Mode:** Batch print mode via `-p` flag:
  ```bash
  claude -p "<prompt>" --cwd "<workspace_dir>"
  ```
- **Status on System:** Currently `UNAUTHENTICATED`.
- **Activation Instructions:**
  To enable Claude Code for autonomous repair, run in an interactive terminal:
  ```bash
  claude auth login
  ```
  Once the browser authentication finishes, JARVIS OS automatically transitions the status to `READY`.

## 2.4 OpenCode Adapter (`tools/agents/adapters/opencode_adapter.py`)
- **Binary:** `opencode` (`/home/roshan/.npm-global/bin/opencode`)
- **Execution Mode:** Non-interactive script mode.
- **Status on System:** `UNAUTHENTICATED` (no remote integration providers configured).

## 2.5 Local Ollama AI Adapter (`tools/agents/adapters/ollama_adapter.py`)
- **Endpoint:** `http://127.0.0.1:11434/api/generate`
- **Execution Mode:** Local HTTP REST API with zero external network dependencies.
- **Payload Schema:**
  ```json
  {
    "model": "llama3.2:1b",
    "prompt": "You are JARVIS OS autonomous diagnostic engineer...",
    "stream": false,
    "options": {
      "temperature": 0.2,
      "num_predict": 128
    }
  }
  ```
- **Capabilities:**
  - 100% offline root-cause analysis and second-opinion patch review.
  - Zero cloud costs, zero token rate limits.
  - Models: `llama3.2:1b` (fast, 1.2s TTFT), `qwen3.5:4b` (complex reasoning).

---

# 3. Agent Scoring & Selection Logic

When a self-healing repair is triggered, `MultiAgentOrchestrator` selects the optimal agent using this scoring algorithm:

```python
score = 0.0
# Readiness check (hard requirement)
if not agent.is_ready:
    return -1.0

# 1. File editing capability (+30 points)
if agent.capabilities.supports_file_editing:
    score += 30.0

# 2. Speed / Latency preference
if agent.id == "antigravity":
    score += 40.0  # High speed on ARM64, cloud backed
elif agent.id == "codex":
    score += 35.0  # Fast reasoning
elif agent.id == "ollama":
    score += 20.0  # Offline guarantee, CPU bound on Pi 5

# 3. Task type affinity
if task_type == "DIAGNOSIS_ONLY":
    if agent.id == "ollama": score += 25.0
if task_type == "MULTI_FILE_REPAIR":
    if agent.id == "antigravity": score += 20.0
```
