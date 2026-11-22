# JARVIS OS Integration Guide — Module 32 (System Health & Diagnostics)

```python
from fastapi import FastAPI
from backend.app.config import SystemHealthConfig
from backend.app.main import mount_module
from backend.services.health_engine import SystemHealthEngine

jarvis_app = FastAPI(title="JARVIS OS Core")
m32_engine = SystemHealthEngine(SystemHealthConfig(db_path="./data/jarvis_system_health.db"))
mount_module(jarvis_app, engine=m32_engine, include_root_ui=False)
```
Mounted routes: `/api/v1/system-health/*`, `/api/v1/system-health/ws/metrics`, `/system-health`, and `jarvis_app.state.system_health`.
