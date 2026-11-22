# JARVIS OS — Smart Resume Matching

Automated skill extraction, candidate qualification scoring, semantic gap analysis, and candidate leaderboards for **Raspberry Pi 5 (8GB)**.

## Features
- **Automated Skill & Experience Extraction (`extractor.py`)**: Extracts technical, robotics, cloud, and soft skills with alias normalization (`ros 2 -> ros2`, `rpi5 -> raspberry pi`, `k8s -> kubernetes`), years of experience, and education level.
- **Qualification Scoring & Semantic Gap Analysis (`matcher.py`)**: Blends required-skill coverage (`45%`), preferred-skill coverage (`15%`), 128-D dense semantic cosine similarity (`25%`), and experience alignment (`15%`) into a `0–100` score with actionable gap recommendations.
- **SQLite WAL Jobs & Candidate Leaderboards (`storage.py`)**: Persists job descriptions and automatically ranks evaluated candidates per role.

## Quick Start (Standalone)
```bash
pip install -r requirements.txt
python3 -m jarvis_resume_matching.app
# Open http://localhost:8025/resume-matching
```

## Run Tests
```bash
python3 -m unittest discover -s jarvis_resume_matching/tests -v
```
