# JARVIS OS — Phase 8 Architecture Guide
## Unified AI Application Platform, Modular Registry, Shared Services & Extensibility Manual

---

## 1. Architectural Philosophy

JARVIS OS Phase 8 introduces the **JARVIS Apps Center**, a unified platform architecture that allows independent AI applications to run side-by-side inside JARVIS OS while sharing core operating system services:
- **Centralized Authentication & RBAC**: ADMIN, USER, and GUEST roles governed with cryptographic PIN hashing and face biometric identity.
- **Unified AI Engine Layer**: Shared abstraction for local inference (Ollama `llama3.2:1b`, `qwen3.5:4b`, `moondream:latest`) and cloud AI providers (Gemini, Claude, OpenAI) with truthful configuration reporting.
- **Hardware Telemetry & Admission Control**: Real-time Linux monitoring (CPU, RAM, root disk, and SoC thermal telemetry) preventing out-of-memory or thermal runaway on the Raspberry Pi 5.
- **Isolated User Storage**: Strict per-user segmentation for application settings, task executions, favorites, and recent usage history.
- **Truthful Lifecycle Enforcement**: Honest, un-simulated state machine distinguishing verified `Available` applications from roadmap `Planned` applications.

---

## 2. Directory Structure

The Apps Center platform components reside in `apps/apps_center/` and `data/apps/`:

```
jarvis-os/
├── apps/
│   ├── api/
│   │   └── apps_center_api.py       # FastAPI router mounted at /api/apps/*
│   └── apps_center/
│       ├── __init__.py              # Package export
│       ├── models.py                # Pydantic v2 domain models
│       ├── registry.py              # Thread-safe manifest loader & search engine
│       ├── database.py              # SQLite migration & user state repository
│       ├── ai_service.py            # Shared AI Service Layer (Ollama/Gemini/Claude/OpenAI)
│       ├── resource_manager.py      # Real hardware metrics & task admission control
│       ├── task_manager.py          # Background asynchronous task queue
│       └── permissions.py           # Multi-tiered RBAC access & launch gatekeeper
├── data/
│   └── apps/
│       └── registry.json            # Canonical JSON registry of 20 applications
├── tests/
│   └── unit/
│       └── test_phase8_apps_center.py # 25-item automated test suite
└── apps/dashboard/static/
    └── index.html                   # Responsive Apps Center dashboard UI & modal
```

---

## 3. The 20 Canonical Applications & Status Rules

In accordance with strict zero-simulation principles, applications in the catalog are partitioned into **Operational** (`available`) and **Roadmap** (`planned`).

### Operational Applications (3 Available)
1. **`voice-assistant`** (`ai_agents`): ReSpeaker Lite USB microphone capture, adaptive VAD, 3-second continuous silence threshold, wake-word detection, and OmniVoice / Edge-TTS fallback.
2. **`face-recognition`** (`computer_vision`): OpenCV Zoo YuNet face detection and SFace 128-D feature embeddings (<90ms on Cortex-A76 CPU), single-camera integration via `http://127.0.0.1:8082`.
3. **`multi-agent-automation`** (`ai_agents`): Multi-AI coding agent orchestrator (Antigravity, Codex, Claude Code, Ollama) with AST syntax checks, Git rollback checkpoints, and stuck-task watchdogs.

### Roadmap Applications (17 Planned)
1. `document-qa` (RAG, PDF/Markdown indexer) — *Designated Phase 9 implementation*
2. `ai-interview` (Interactive technical/behavioral interview coach)
3. `study-planner` (Spaced-repetition curriculum scheduler)
4. `learning-coach` (Socratic tutoring and diagnostics)
5. `speech-translation` (Streaming bilingual translation & TTS)
6. `youtube-summarizer` (Transcript extraction & chaptering)
7. `research-assistant` (Multi-source literature synthesis & citations)
8. `web-scraper` (Scheduled rate-limited web crawlers)
9. `coding-assistant` (Local code refactoring and test synthesis)
10. `ai-search-engine` (Hybrid BM25 + dense neural retrieval)
11. `customer-support` (Ticket triage and domain FAQ assistant)
12. `recommendation-engine` (Two-tower neural user preference model)
13. `fraud-detection` (Audit log anomaly detection)
14. `resume-matching` (NER candidate qualification scoring)
15. `social-media-saas` (Content scheduling and copy generation)
16. `content-creation` (Multi-stage blog and scriptwriting engine)
17. `trading-bot` (Paper-trading market simulation with guardrails)

> [!IMPORTANT]
> Attempting to launch any `planned` application via REST API or voice command is explicitly blocked with HTTP 400 and an honest roadmap description.

---

## 4. How to Implement a New Application (e.g., Phase 9 Document Q&A)

To transition a Planned application to Available, follow this standardized 6-step integration pattern:

### Step 1: Update Application Manifest in `data/apps/registry.json`
Change `status` from `"planned"` to `"available"` and set its `route` and `target_tab`:
```json
{
  "id": "document-qa",
  "name": "Document Question Answering",
  "version": "1.0.0",
  "status": "available",
  "route": "/apps/document-qa",
  "target_tab": "document-qa",
  "minimum_role": "USER",
  "permissions": ["filesystem_read", "shared_ai_inference"],
  "capabilities": ["document_indexing", "vector_embeddings", "semantic_search", "qa_synthesis"],
  "resource_profile": "medium",
  "inference_type": "hybrid",
  "lifecycle_state": "active"
}
```

### Step 2: Implement Domain Logic in `apps/apps_center/plugins/<app_id>/`
Create a dedicated package:
```python
# apps/apps_center/plugins/document_qa/service.py
from apps.apps_center.ai_service import shared_ai
from apps.apps_center.resource_manager import resource_manager

class DocumentQAService:
    async def index_document(self, file_path: str):
        # 1. Check resource capacity
        is_admitted, reason = resource_manager.check_admission("medium")
        if not is_admitted:
            raise RuntimeError(f"System overloaded: {reason}")
        
        # 2. Extract embeddings using shared AI
        embeddings = await shared_ai.generate_embeddings(text, provider="ollama")
        ...
```

### Step 3: Register REST Endpoints in `apps/api/`
Mount your router in `apps/core/main.py`:
```python
# apps/api/document_qa_api.py
from fastapi import APIRouter, Depends, HTTPException
from apps.apps_center.permissions import apps_permissions

router = APIRouter(prefix="/api/apps/document-qa", tags=["Document QA"])

@router.post("/query")
async def query_documents(req: QueryRequest):
    ...
```

### Step 4: Add Background Task Execution via `TaskManager`
For long-running operations (such as document indexing or paper backtesting), wrap execution in a managed task:
```python
from apps.apps_center.task_manager import app_task_manager

task_id = app_task_manager.submit_task(
    app_id="document-qa",
    user_id=current_user,
    coroutine_func=service.index_document,
    file_path=path
)
```

### Step 5: Add UI Tab in `apps/dashboard/static/index.html`
Add the tab button to the desktop navigation bar and create a corresponding container `<div id="document-qa-tab" class="tab-pane">`.

### Step 6: Verify with Automated Tests
Write test cases in `tests/unit/test_app_<id>.py` validating:
- Manifest integrity
- Role restrictions (ADMIN/USER/GUEST)
- Resource admission throttling
- Per-user data isolation
- Honest error reporting when models or dependencies are unavailable

---

## 5. Security & Isolation Model

1. **Localhost Binding**: All Apps Center endpoints bind strictly to `127.0.0.1:8000`. No 0.0.0.0 listeners.
2. **Credential Redaction**: Cloud API keys are stored in `provider_configurations` with secret masking (`sk-ant-***`). Raw credentials are never returned over public endpoints.
3. **Database Security**: SQLite WAL mode enabled with parameterized queries across all state tables.
4. **Single Camera Ownership**: The Sony IMX708 sensor is accessed solely through `jarvis-camera.service` on loopback port 8082, preventing hardware resource locks.
