# JARVIS OS — Feature #4: AI Social Media Automation

Strictly additive, Raspberry Pi 5-friendly Business & Support module for **JARVIS OS**:
- **Multi-Platform Content Planner & Copy Generator** (LinkedIn, X/Twitter with 280-char guard, Instagram, YouTube) via OpenRouter `openrouter/free`, Local Ollama, or deterministic offline templates
- **Scheduled Publishing Queue** with safe `dry_run=True` default, optional webhook bridge (`JARVIS_SOCIAL_WEBHOOK_URL` for n8n/Make/Zapier), and automatic ready-to-post `.md` manual export fallback
- **Engagement Analytics Dashboard** (impressions, likes, comments, shares, clicks, Engagement Rate %, CTR %, and per-platform breakdown)
- **SQLite (WAL Mode) Storage** + **JARVIS OS Dark Cyber Web UI** at `/social-automation`

## Quick Start (Standalone on Raspberry Pi 5)

```bash
cd ~/.gemini/antigravity/scratch/jarvis-os
unzip /path/to/jarvis_ai_social_automation.zip -d features/
cd features

export OPENROUTER_API_KEY="your-openrouter-key"
uvicorn jarvis_ai_social_automation.app:app --host 127.0.0.1 --port 8014
```

Open `http://127.0.0.1:8014/social-automation`.

## Run Tests

```bash
python3 -m unittest discover -s jarvis_ai_social_automation/tests -v
# or with pytest:
pytest jarvis_ai_social_automation/tests -v
```
