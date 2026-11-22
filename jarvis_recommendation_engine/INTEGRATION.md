# Integrating Deep Learning Recommendation Engine into JARVIS OS

This package is **strictly additive** — it does not modify or overwrite any existing JARVIS OS files.

## 1. Copy the Package
Copy the `jarvis_recommendation_engine/` folder into your JARVIS OS repository (for example, `~/.gemini/antigravity/scratch/jarvis-os/jarvis_recommendation_engine/`).

## 2. Mount the Router in Your JARVIS FastAPI App
In your main FastAPI backend, mount the router with two lines:

```python
from jarvis_recommendation_engine import RecommendationConfig, create_router

app.include_router(create_router(RecommendationConfig()))
```

## 3. Environment Variables (Optional)
- `JARVIS_REC_DB_PATH`: Custom SQLite WAL database path (default: `.jarvis_recommendation_engine/recommendations.db`).
- `JARVIS_REC_EMBED_DIM`: Dense embedding dimension (default: `128`).
- `JARVIS_REC_LATENT_DIM`: SGD latent factor dimension (default: `16`).
- `JARVIS_REC_PORT`: Standalone server port when run via `app.py` (default: `8019`).

## 4. Endpoints Added
- `GET /recommendations` — Interactive JARVIS OS web dashboard
- `GET /api/recommendations/health` — Engine status, embedding dimension, and item/interaction counts
- `POST /api/recommendations/items` — Upsert catalog item and compute 128-D dense embedding
- `GET /api/recommendations/items` — List all catalog items
- `POST /api/recommendations/interactions` — Record user interaction (`view`, `like`, `bookmark`, `complete`, `dismiss`, or explicit rating)
- `POST /api/recommendations/recommend` — Get hybrid personalized recommendations
- `GET /api/recommendations/items/{item_id}/similar` — Find cosine-similar catalog items

## 5. Dashboard Card Update
Once mounted, update the **Deep Learning Recommendation Engine** card in your JARVIS OS dashboard from `PLANNED` to `AVAILABLE` and point its **Open** button to `/recommendations`.
