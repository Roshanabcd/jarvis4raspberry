# Integration Guide — JARVIS OS Module 20 (`v1.0.0`)

```python
from backend.app.main import mount_module
engine = mount_module(app, include_root_ui=False)
```
Exposes `/conversational-ai` UI and `/api/v1/conversational-ai/*` REST + WebSocket APIs. Bind future Module 22 (Intelligent AI Model Router) by subclassing `ConversationalProviderAdapter`.
