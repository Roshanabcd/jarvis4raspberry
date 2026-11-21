# JARVIS OS Integration Guide — Module 34 (Personal Finance Manager)

```python
from fastapi import FastAPI
from backend.app.config import FinanceConfig
from backend.app.main import mount_module
from backend.services.finance_engine import FinanceEngine

jarvis_app = FastAPI(title="JARVIS OS Core")
m34_engine = FinanceEngine(FinanceConfig(db_path="./data/jarvis_finance.db"))
mount_module(jarvis_app, engine=m34_engine, include_root_ui=False)
```
Mounted routes: `/api/v1/finance/*`, `/api/v1/finance/ws/updates`, `/finance`, and `jarvis_app.state.finance`.
