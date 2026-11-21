# JARVIS OS Integration Guide — Module 35 (Visual Workflow Builder)

```python
from fastapi import FastAPI
from backend.app.config import WorkflowConfig
from backend.app.main import mount_module
from backend.services.workflow_engine import WorkflowEngine

jarvis_app = FastAPI(title="JARVIS OS Core")
m35_engine = WorkflowEngine(WorkflowConfig(db_path="./data/jarvis_workflows.db"))
mount_module(jarvis_app, engine=m35_engine, include_root_ui=False)
```
Mounted routes: `/api/v1/workflows/*`, `/api/v1/workflows/ws/runs`, `/workflows`, and `jarvis_app.state.workflows`.
