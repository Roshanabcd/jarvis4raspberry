# JARVIS OS — Deep Learning Recommendation Engine

Hybrid personalized content and task recommendation module built for **JARVIS OS** on **Raspberry Pi 5 (8GB)** with zero heavy PyTorch/TensorFlow dependencies.

## Features
- **128-D Dense Semantic Embeddings**: Pure-Python L2-normalized word + character trigram projections with cosine similarity (`embeddings.py`).
- **Hybrid Scoring Engine**: Blends content embedding cosine similarity (`0.45`), item-item collaborative filtering (`0.35`), and SGD latent-factor matrix factorization (`0.20`), plus a cold-start popularity fallback (`recommender.py`, `engine.py`).
- **SQLite WAL Persistence**: Stores catalog items, 128-D embeddings, and weighted user interactions (`view`, `like`, `bookmark`, `complete`, `dismiss`) in WAL mode with foreign keys (`storage.py`).
- **JARVIS Dark Cyber Dashboard**: Interactive web UI at `/recommendations` for catalog management, interaction logging, personalized rankings, and item-to-item similarity (`static/index.html`).

## Quick Start (Standalone)
```bash
pip install -r requirements.txt
python3 -m jarvis_recommendation_engine.app
# Open http://localhost:8019/recommendations
```

## Run Tests
```bash
python3 -m unittest discover -s jarvis_recommendation_engine/tests -v
```
