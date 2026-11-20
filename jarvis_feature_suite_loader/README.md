# JARVIS OS — Unified Feature Suite Loader

Mounts all **16 additive JARVIS OS feature modules** (Features #1–#15 + Handwritten to Text Converter) in **2 lines of Python** with a unified dark-cyber launchpad at `/suite` and live health aggregation at `/api/suite/health`.

## Mount into Existing JARVIS OS (2 Lines)
Unzip whichever feature packages you want into your JARVIS OS directory (e.g. `~/.gemini/antigravity/scratch/jarvis-os/`), alongside `jarvis_feature_suite_loader/`, then add:

```python
from jarvis_feature_suite_loader import mount_jarvis_feature_suite

mount_jarvis_feature_suite(app)
```

Missing modules are gracefully marked `NOT_INSTALLED` without ever crashing your main JARVIS OS backend.

## Run Standalone (All 16 Modules Together)
```bash
python3 -m jarvis_feature_suite_loader.app
# Open http://localhost:8010/suite
```

## Run Integration Tests
```bash
python3 -m unittest discover -s jarvis_feature_suite_loader/tests -v
```
