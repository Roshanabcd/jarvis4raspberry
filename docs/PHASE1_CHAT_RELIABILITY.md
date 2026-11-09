# JARVIS OS — Phase 1 Chat Reliability & Stale Response Elimination

## 1. Root Cause Discovery

Prior to Phase 1 repairs, the JARVIS chat interface exhibited severe reliability defects:
1. **Intent Hijacking:** Regex patterns in `LocalIntelligenceEngine` searched for standalone terms such as `\b(ram|uptime)\b`. Consequently, requests like *"Write a Python script to display system uptime and memory"* were intercepted as hardware status commands, returning current machine telemetry instead of generating Python code.
2. **Global Conversation Pollution:** `JARVISBrain` stored messages in a single shared list (`self._history`). Inquiries from different sessions or browser tabs polluted the same context window.
3. **Missing Correlation IDs:** Streamed chunks and synchronous responses lacked unique request and message identifiers, creating vulnerability to race conditions where older asynchronous completions could overwrite newer interactions.
4. **TTS Blocking Text Generation:** Chat responses were paused while speech synthesis processed the audio file, causing perceived UI freezes and delayed text rendering.

---

## 2. Architectural Repairs Implemented

### A. Intent Protection for Programming & Explanations
`LocalIntelligenceEngine.classify_intent()` now evaluates queries through strict guard clauses before applying hardware regex rules:
- Queries requesting code creation (`write`, `create`, `code`, `implement`, `script`, `function`, `fibonacci`, `algorithm`) immediately route to the neural language model (`"general"`).
- Requests containing standalone numbers (`"2020"`) route to `standalone_number`, prompting for user clarification rather than fabricating telemetry.
- Conversational recall inquiries (*"What was my first question?"*) route to `history_recall` to query session context.

### B. Unique Request & Message Correlation
Every incoming interaction is tagged with:
- `request_id`: `req_<uuid4_hex>` (correlates stream events to the initiating request).
- `message_id`: `msg_<uuid4_hex>` (unique ID for both user and assistant turns).
- `session_id`: Unique identifier isolating independent dialogue threads.
- `timestamp`: Epoch floating-point timestamp.

### C. Persistent Session Isolation (SQLite WAL-Mode)
Sessions are completely isolated in `memory/long_term/database.py` under the `conversation_messages` table:
```sql
CREATE TABLE IF NOT EXISTS conversation_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT    NOT NULL,
    request_id  TEXT,
    message_id  TEXT    UNIQUE NOT NULL,
    role        TEXT    NOT NULL,
    content     TEXT    NOT NULL,
    timestamp   REAL    NOT NULL,
    provider    TEXT,
    model       TEXT,
    tools_used  TEXT    DEFAULT '[]',
    status      TEXT    DEFAULT 'completed',
    error       TEXT
);
```

### D. Text-First Delivery Invariant
Text is delivered immediately:
- In SSE streaming (`POST /api/chat/stream`), tokens appear in real time in the chat bubble.
- The completion event (`type: "done"`) is emitted as soon as the language model finishes.
- Speech synthesis is strictly optional and only triggered post-stream when `speak: true`. Displayed text is never modified or delayed by audio generation.

### E. User Cancellation Support
When the user clicks **Stop** in the UI, an `AbortController` signals the SSE stream. The backend generator closes cleanly via `generator.close()`, releasing system resources without orphaned background threads.
