# JARVIS OS — Feature #2: AI Content Creation Pipeline

Strictly additive, Raspberry Pi 5-friendly Media & Content module for **JARVIS OS**:
- **Technical Blog Generator** (SEO title, meta description, structured Markdown sections, code blocks, read-time estimate)
- **Short-Video Script Generator** (timestamped beats, spoken dialogue, visual/B-roll cues for YouTube Shorts, Reels, TikTok)
- **Hooks & Platform Captions** (categorized hooks + platform-sized captions & hashtags for YouTube, LinkedIn, Instagram, X)
- **Carousel Outline Builder** (slide-by-slide cover, problem, numbered value slides, and closing CTA)
- **One-Click Full Campaign Bundle** (generates all 4 formats together + downloadable `.md` export)
- **SQLite (WAL Mode) Content Library** + **JARVIS OS Dark Cyber Web UI** at `/content-pipeline`

## Quick Start (Standalone on Raspberry Pi 5)

```bash
cd ~/.gemini/antigravity/scratch/jarvis-os
unzip /path/to/jarvis_ai_content_pipeline.zip -d features/
cd features

export OPENROUTER_API_KEY="your-openrouter-key"
uvicorn jarvis_ai_content_pipeline.app:app --host 127.0.0.1 --port 8012
```

Open `http://127.0.0.1:8012/content-pipeline`.

## Run Tests

```bash
python3 -m unittest discover -s jarvis_ai_content_pipeline/tests -v
# or with pytest:
pytest jarvis_ai_content_pipeline/tests -v
```
