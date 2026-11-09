# JARVIS OS — Phase 5 Agent Discovery Specification
## Real-Time Discovery, Authentication Verification & Capability Auditing

---

# 1. Discovery Methodology & Truthfulness Guarantee

JARVIS OS does **not** rely on simulated or hardcoded agent lists. The `AgentRegistry` (`tools/agents/registry.py`) performs active filesystem and process inspection to discover installed AI coding agents on Raspberry Pi 5 ARM64.

### Strict Truthfulness Contract:
1. **Never mark an agent `READY` based merely on binary presence.** An agent is only marked `READY` if both binary execution and authenticated session verification pass.
2. **Never expose credentials.** Authentication verification must inspect CLI return codes or scrubbed output streams without logging or displaying tokens, passwords, or API keys.
3. **Persist state gracefully.** Discovery results are cached to `data/agents/registry.json` and updated automatically upon health checks or explicit refresh commands.

---

# 2. System Discovery Baseline (Raspberry Pi 5 ARM64)

Audited on November 9, 2026:

| Agent Name | Provider | Binary / Endpoint | Detected Version | Auth Status | Verification Mechanism | Status |
|---|---|---|---|---|---|---|
| **Google Antigravity** | Google DeepMind | `/home/roshan/.local/bin/agy` | `1.5.3` | **True** | `agy models` exit code 0 | **`READY`** |
| **OpenAI Codex** | OpenAI | `/home/roshan/.local/bin/codex` | `codex-cli 0.152.1` | **True** | `codex login status` (stderr check) | **`READY`** |
| **Anthropic Claude Code** | Anthropic | `/home/roshan/.local/bin/claude` | `2.1.241 (Claude Code)` | **False** | `claude auth status` (`loggedIn: false`) | **`UNAUTHENTICATED`** |
| **OpenCode** | OpenCode Community | `/home/roshan/.npm-global/bin/opencode` | `v2.0.22` | **False** | `opencode auth list` (no integrations) | **`UNAUTHENTICATED`** |
| **Local Ollama AI** | Ollama Foundation | `http://127.0.0.1:11434` | `0.5.x` | **True** | HTTP `GET /api/tags` -> 200 OK | **`READY`** |

---

# 3. Detailed Agent Verification Mechanics

### 3.1 Google Antigravity (`agy`)
- **Binary Path:** `/home/roshan/.local/bin/agy`
- **Version Detection:** `agy --version` returns `1.5.3`.
- **Authentication Check:** Runs `agy models` with a 5-second timeout. When logged in, it lists available models (`gemini-3.8-flash-high`, `claude-sonnet-4-6`, `gpt-oss-120b-medium`) with returncode 0.
- **Capabilities:** Non-interactive execution (`-p`), file editing (`--add-dir`), structured output, sandboxing.

### 3.2 OpenAI Codex CLI (`codex`)
- **Binary Path:** `/home/roshan/.local/bin/codex`
- **Version Detection:** `codex --version` returns `codex-cli 0.152.1`.
- **Authentication Check:** Executes `codex login status`. Codex outputs `"Logged in using ChatGPT"` to `stderr` with exit code 0. Adapter captures both `stdout` and `stderr` to verify active login truthfully.
- **Capabilities:** Non-interactive execution (`codex exec`), project editing, git reviews (`codex review`).

### 3.3 Anthropic Claude Code CLI (`claude`)
- **Binary Path:** Symlinked to `/home/roshan/.local/bin/claude` from `@anthropic-ai/claude-agent-sdk-linux-arm64`.
- **Version Detection:** `claude --version` returns `2.1.241 (Claude Code)`.
- **Authentication Check:** Runs `claude auth status` which returns JSON: `{"loggedIn": false, "authMethod": "none"}`. Correctly categorized as `UNAUTHENTICATED` until the user executes interactive web authorization.
- **Zero Hallucination:** JARVIS OS informs the user truthfully that Claude Code is installed but requires logging in before it can accept autonomous tasks.

### 3.4 OpenCode CLI (`opencode`)
- **Binary Path:** `/home/roshan/.npm-global/bin/opencode`
- **Version Detection:** `opencode --version` returns `opencode v2.0.22`.
- **Authentication Check:** Runs `opencode auth list` returning `"No authenticated integrations found"`. Correctly categorized as `UNAUTHENTICATED`.

### 3.5 Local Ollama AI (`ollama`)
- **Endpoint:** `http://127.0.0.1:11434`
- **Version Detection:** Queried via HTTP `GET /api/version` returning version `0.5.x`.
- **Model Inspection:** HTTP `GET /api/tags` queries installed models on disk: `llama3.2:1b` (1.32 GB) and `qwen3.5:4b` (3.39 GB).
- **Authentication:** Local host binding; 100% offline, zero cloud tokens required.

---

# 4. Storage & Registry Schema

Discovered agent metadata is written to `data/agents/registry.json`:

```json
{
  "antigravity": {
    "id": "antigravity",
    "display_name": "Google Antigravity",
    "installed": true,
    "authenticated": true,
    "version": "1.5.3",
    "cli_path": "/home/roshan/.local/bin/agy",
    "capabilities": {
      "supports_noninteractive": true,
      "supports_file_editing": true,
      "supports_shell": true,
      "supports_structured_output": true,
      "supports_review": true,
      "supports_sandbox": true,
      "models": ["gemini-3.8-flash-high", "claude-sonnet-4-6"]
    },
    "permission_mode": "workspace_scoped",
    "status": "READY",
    "error_message": null
  }
}
```
