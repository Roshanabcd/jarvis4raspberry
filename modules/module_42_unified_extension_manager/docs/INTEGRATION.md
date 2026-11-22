# Integration Guide — JARVIS Module 42 & Shared SDK

## 1. Standalone Inspection of Modules 18–41 on Raspberry Pi 5
1. Start Module 42 (`./scripts/run.sh`) on port `8142`.
2. Open `http://127.0.0.1:8142/extensions` and scan `/home/roshan/Downloads/module-jarvis`.
3. Review each module's compatibility report (`verified_compatibility`, `inferred_from_metadata`, `unverified_requirements`, `conflicts`, `unsupported_dependencies`).
4. Click **Dry-Run Install Plan** to obtain the dependency-ordered integration plan, permission summary, and rollback instructions before using Antigravity to merge modules into your JARVIS Core repo.

## 2. Mounting into an Existing JARVIS FastAPI Core
```python
from fastapi import FastAPI
from backend.app.config import ExtensionManagerConfig
from backend.app.main import mount_module
from backend.services.extension_manager import ExtensionManager

host_app = FastAPI(title="JARVIS Core")
cfg = ExtensionManagerConfig(db_path="./data/jarvis_extensions.db")
manager = mount_module(host_app, manager=ExtensionManager(config=cfg), include_root_ui=False)
```

## 3. Building New Extensions with `sdk/jarvis_sdk`
See `sample_extension/extension.py` for a working reference extension using `ReferenceHostAdapter`, `ModuleRegistration`, `HealthCheckResult`, `StructuredLogger`, and `EventBus`.

## 4. Lazy Loading & Resource Efficiency on 8 GB RAM Hosts
Module 42 never auto-starts discovered module servers or loads heavyweight AI models during scanning or registration. Heavyweight modules (e.g., `torch`, `opencv-python`, `playwright`) are automatically flagged with an isolated-service integration recommendation.
