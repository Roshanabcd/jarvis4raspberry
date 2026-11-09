# JARVIS OS — Phase 5 Agent Security Specification
## Zero-Trust Architecture, Secret Scrubbing, Process Isolation & Safety Boundaries

---

# 1. Security Philosophy: Zero-Trust AI Execution

In JARVIS OS, AI coding agents are treated as semi-trusted external actors. While they possess powerful diagnostic and reasoning capabilities, they must operate within strictly demarcated sandboxes to prevent:
1. Leakage of private user credentials, API keys, and environment variables.
2. Accidental corruption or deletion of system files.
3. Modification of files outside approved workspaces.
4. Unauthorized hardware actuation.

---

# 2. Secret Redaction & Scrubbing Pipeline

The `ProblemContextPackager` (`tools/agents/context_packager.py`) applies automated sanitization before constructing any context dictionary:

### 2.1 Prohibited Files List
The following file names and extensions are blocked from being packaged into agent prompts:
- `.env`, `.env.local`, `.env.production`, `.env.staging`
- `id_rsa`, `id_ed25519`, `authorized_keys`, `known_hosts`
- `cookies.txt`, `credentials.json`, `secrets.yaml`, `service_account.json`
- `*.pem`, `*.key`, `*.p12`, `*.pfx`

### 2.2 In-Text Secret Pattern Matching
Regex patterns continuously scan tracebacks, code snippets, and error logs:
- `ghp_[a-zA-Z0-9]{36}` (GitHub Personal Access Tokens)
- `sk-[a-zA-Z0-9]{32,}` (OpenAI / Anthropic Secret Keys)
- `AIzaSy[a-zA-Z0-9_\-]{33}` (Google Cloud / Gemini API Keys)
- `(?i)(?:password|token|secret|auth)[\s:=]+['"][^'"]+['"]`

Matches are replaced with `[REDACTED_SECRET]`.

---

# 3. Environment Variable Sanitization

When spawning child processes (`agy`, `codex`, `claude`, `pytest`), the orchestrator passes a sanitized environment dictionary:
- Sensitive system keys (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `HF_TOKEN`, `GITHUB_TOKEN`) are removed unless strictly required by a verified adapter.
- `DISPLAY=:0` is preserved for graphical window awareness.
- `PYTHONPATH` is explicitly scoped to the project root.

---

# 4. Process Isolation & Resource Limits

1. **Process Groups (`os.setsid`):** Agent processes are spawned in independent process sessions, ensuring that terminating an agent cleanly terminates all sub-processes without leaving orphaned zombies.
2. **CPU & Memory Ceilings:** The stuck-task watchdog kills processes that exceed 120 seconds or stagnate for >60 seconds.
3. **Mutex Concurrency Lock:** Only 1 coding agent is permitted write access at any time, preventing race conditions and file collisions.
