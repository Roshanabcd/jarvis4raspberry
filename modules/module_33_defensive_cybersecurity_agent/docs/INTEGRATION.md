# JARVIS OS Integration Guide — Module 33 (Defensive Cybersecurity Agent)

```python
from fastapi import FastAPI
from backend.app.config import CyberSecurityConfig
from backend.app.main import mount_module
from backend.services.security_engine import DefensiveSecurityEngine

jarvis_app = FastAPI(title="JARVIS OS Core")
m33_engine = DefensiveSecurityEngine(
    CyberSecurityConfig(db_path="./data/jarvis_cybersecurity.db", scan_root="/home/roshan/.gemini/antigravity/scratch/jarvis-os")
)
mount_module(jarvis_app, engine=m33_engine, include_root_ui=False)
```
Mounted routes: `/api/v1/cybersecurity/*`, `/api/v1/cybersecurity/ws/alerts`, `/cybersecurity`, and `jarvis_app.state.cybersecurity`.
