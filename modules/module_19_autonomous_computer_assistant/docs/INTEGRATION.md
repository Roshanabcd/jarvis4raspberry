# Integration Guide — JARVIS OS Module 19 (`v1.0.0`)

## Additive FastAPI Mount
```python
from backend.app.main import mount_module
engine = mount_module(app, include_root_ui=False)
```
Exposes UI at `/computer-assistant` and APIs under `/api/v1/computer-assistant/*`.

## Replacing SafeDemoDesktopAdapter for Real Host Control
Implement `DesktopAutomationAdapter` from `backend/adapters/contracts.py` and pass it into `ComputerAssistantEngine(adapter=YourLiveAdapter())` only after configuring OS permissions and authentication (Module 40).
