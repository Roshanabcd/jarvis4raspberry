# JARVIS OS — Feature #8: ChatGPT-Powered Customer Support Bot

Strictly additive, Raspberry Pi 5-friendly Business & Support module for **JARVIS OS**:
- **Domain Knowledge Base & Inquiry Answering** (grounded in your SQLite KB via OpenAI ChatGPT, OpenRouter `openrouter/free`, Local Ollama, or deterministic offline KB fallback)
- **Sentiment Classification** (`POSITIVE`, `NEUTRAL`, `NEGATIVE`, `URGENT_FRUSTRATED` with `-1.0..+1.0` score)
- **Automated Ticket Triage & Escalation Routing** (`P1_CRITICAL`–`P4_LOW`, routed to `security-oncall`, `billing-specialists`, `tier2-engineering`, `identity-support`, or `ai-tier1-support`)
- **SQLite (WAL Mode) Ticket Queue & Stats** + **JARVIS OS Dark Cyber Web UI** at `/support-bot`

## Quick Start (Standalone on Raspberry Pi 5)

```bash
cd ~/.gemini/antigravity/scratch/jarvis-os
unzip /path/to/jarvis_customer_support_bot.zip -d features/
cd features

export OPENROUTER_API_KEY="your-openrouter-key" # or OPENAI_API_KEY
uvicorn jarvis_customer_support_bot.app:app --host 127.0.0.1 --port 8018
```

Open `http://127.0.0.1:8018/support-bot`.

## Run Tests

```bash
python3 -m unittest discover -s jarvis_customer_support_bot/tests -v
# or with pytest:
pytest jarvis_customer_support_bot/tests -v
```
