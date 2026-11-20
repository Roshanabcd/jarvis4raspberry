# JARVIS OS — PHASE 11: YOUTUBE VIDEO SUMMARIZER ARCHITECTURE

**Application ID:** `youtube-summarizer`  
**Display Name:** `YouTube Video Summarizer`  
**Target Architecture:** ARM64 / Raspberry Pi 5 (8GB RAM), Debian 13 Trixie  
**Route / Endpoint:** `/apps/youtube-summarizer` -> Tab `#tab-youtube` (`/api/youtube/*`)  
**Status:** IMPLEMENTED & VERIFIED  

---

## 1. Architectural Overview & System Flow

JARVIS YouTube AI is designed with strict adherence to YouTube Developer Policies, eliminating unauthorized scraping or downloading while maximizing user productivity through multi-format AI summarization, timestamped chapterization, semantic transcript retrieval, and grounded conversational assistance.

```
                                 [ YouTube URL / ID ]
                                          |
                                          v
                         +----------------------------------+
                         |  url_parser.py                   |
                         |  - 11-char ID extraction         |
                         |  - Scheme & Host Allowlist       |
                         |  - SSRF & Private Network Block  |
                         +----------------------------------+
                                          |
                                          v
                         +----------------------------------+
                         |  metadata.py                     |
                         |  - YouTube Data API v3 (Auth)    |
                         |  - Public oEmbed (Unauth Fallback|
                         |  - ISO 8601 Duration Parser      |
                         +----------------------------------+
                                          |
                 +------------------------+------------------------+
                 |                                                 |
                 v                                                 v
  [ Authorized Caption Track ]                    [ User Media / File Upload ]
  - Creator OAuth Captions                        - Subtitle (.srt, .vtt, .txt, .json)
  - Google API Client                             - Local Media (WAV/MP4/MKV)
                 |                                  with Rights Confirmation Gate
                 v                                                 |
  +----------------------------------------------------------------+
  |  transcripts.py                                                |
  |  - parse_srt, parse_vtt, parse_txt, parse_json                 |
  |  - HTML tag stripping & speaker extraction                     |
  |  - FFmpeg 16kHz mono WAV conversion + Whisper Transcription    |
  |  - Truthful UNAVAILABLE handler with 4 authorized choices      |
  +----------------------------------------------------------------+
                                          |
                                          v
                         +----------------------------------+
                         |  indexing.py                     |
                         |  - Boundary-preserving Chunking  |
                         |  - Exact Timestamp Tracking      |
                         |  - TF-IDF Vector Space Index     |
                         |  - Inverted Keyword Token Index  |
                         +----------------------------------+
                                          |
         +--------------------------------+--------------------------------+
         |                                                                 |
         v                                                                 v
+-----------------------------------+             +-----------------------------------+
|  summarizer.py                    |             |  qa.py                            |
|  - 12 Distinct Summary Formats    |             |  - Multi-chunk Context Retrieval  |
|  - Creator vs AI Chapters         |             |  - Prompt Injection Quarantine    |
|  - Key Info Extractor (Topics,    |             |  - Grounded Answer Guarantee      |
|    Concepts, Dates, Quotes, Facts)|             |  - Truthful Missing Data Notice   |
|  - Prompt Injection Quarantine    |             |  - Deterministic Extractive QA    |
+-----------------------------------+             +-----------------------------------+
         |                                                                 |
         +--------------------------------+--------------------------------+
                                          |
                                          v
                         +----------------------------------+
                         |  database.py                     |
                         |  - SQLite WAL (youtube_notes.db) |
                         |  - User-Isolated Notes & History |
                         |  - Export: MD, JSON, TXT         |
                         +----------------------------------+
                                          |
                                          v
                         +----------------------------------+
                         |  apps/api/youtube_api.py         |
                         |  - FastAPI Endpoints             |
                         |  - RBAC (USER / ADMIN)           |
                         +----------------------------------+
                                          |
                                          v
                         +----------------------------------+
                         |  apps/dashboard/static/          |
                         |  - Tab #tab-youtube              |
                         |  - 11 Functional UI Sections     |
                         |  - Voice Assistant Intents       |
                         +----------------------------------+
```

---

## 2. Component Design & Responsibilities

### 2.1 URL Parsing & SSRF Defense (`apps/youtube/url_parser.py`)
- **Supported Formats:** Standard watch (`youtube.com/watch?v=...`), short link (`youtu.be/...`), embed (`youtube.com/embed/...`), Shorts (`youtube.com/shorts/...`), mobile (`m.youtube.com`), and YouTube Music (`music.youtube.com`).
- **SSRF Defenses:**
  - Protocol scheme locked to `http` and `https`.
  - Prohibits embedded userinfo credentials (`user:pass@host`).
  - Prohibits non-standard ports (strictly allows ports 80 and 443).
  - Evaluates host against RFC 1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback (`127.0.0.0/8`), link-local/cloud metadata (`169.254.0.0/16`), and IPv6 equivalents (`::1`, `fc00::/7`, `fe80::/10`).
  - Blocks bare IP addresses (YouTube is only served on authorized hostnames).

### 2.2 Metadata Service (`apps/youtube/metadata.py`)
- **Primary:** YouTube Data API v3 (`videos.list?part=snippet,contentDetails,status`) using configured API key.
- **Fallback:** Public YouTube oEmbed API (`https://www.youtube.com/oembed?url=...&format=json`).
- **Guarantees:** Never fabricates fake video titles, channels, or durations if unauthenticated; parses ISO 8601 durations (`PT15M33S` -> 933 seconds).

### 2.3 Authorized Transcript Ingestion (`apps/youtube/transcripts.py`)
- **Zero Scraping Policy:** No Innertube scraping, no DOM scraping, no `yt-dlp` media extraction.
- **Authorized Channels:**
  1. User-uploaded subtitles (`.srt`, `.vtt`, `.txt`, `.json`).
  2. Creator-owned caption tracks via official YouTube Data API v3 OAuth (`captions.download`).
  3. Local media transcription using FFmpeg + Whisper for user-provided video/audio files with explicit user rights confirmation.
- **Truthful Handling:** When no authorized source is available, returns `TRANSCRIPT_UNAVAILABLE` with clear policy explanation and the 4 authorized acquisition options.

### 2.4 Indexing & Retrieval Engine (`apps/youtube/indexing.py`)
- **Boundary-Preserving Chunking:** Segments are aggregated into chunks targeting 150-250 words without truncating sentences.
- **Precise Timestamp Preservation:** Each chunk preserves exact start timestamp of its opening segment and end timestamp of its closing segment.
- **Hybrid Search Index:** Combines TF-IDF cosine similarity vectors with inverted keyword coverage scoring.

### 2.5 Summarizer & Chapters (`apps/youtube/summarizer.py`)
- **12 Comprehensive Summary Formats:**
  1. `quick`: Crisp executive takeaways.
  2. `detailed`: In-depth multi-section analysis.
  3. `executive`: Strategic implications and decisions.
  4. `key_points`: Bulleted high-impact points.
  5. `chapters`: Chronological chapter breakdowns.
  6. `concepts`: Defined terms and core foundations.
  7. `action_items`: Actionable next steps and tools.
  8. `study_notes`: High-yield revision guide.
  9. `faq`: Question and answer pairs.
  10. `revision`: Quick cheat sheet.
  11. `pros_cons`: Strengths, limitations, and trade-offs.
  12. `technical`: Technical implementation and architectures.
- **Chapter Attribution:** Distinguishes between `CREATOR_PROVIDED_CHAPTER` (parsed from video description timestamps) and `AI_GENERATED_CHAPTER` (synthesized from transcript chunk boundaries).
- **Key Information Extraction:** Structured `KeyInformation` object containing topics, terminology, concepts, facts, dates/numbers, action items, and quotes.

### 2.6 Grounded Conversational Q&A (`apps/youtube/qa.py`)
- Retrieves top matching transcript chunks via `TranscriptIndex`.
- Strict Prompt Injection Quarantine: Encloses transcript excerpts inside `<transcript_context>` tags and mandates that LLMs never execute instructions or role reversals embedded in transcript data.
- Strict Grounding Contract: If the answer is not supported by the transcript, responds with:
  `"I could not find sufficient supporting information in the available transcript."`

### 2.7 Storage & Multi-Tenant Isolation (`apps/youtube/database.py`)
- SQLite database at `data/youtube_notes.sqlite3` with Write-Ahead Logging (WAL).
- User isolation: All notes and activity history filter by `user_id`.
- Export formats: Markdown, JSON, Text.

---

## 3. Data Schema

```sql
CREATE TABLE IF NOT EXISTS videos (
    video_id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    channel_title TEXT,
    channel_id TEXT,
    duration_seconds INTEGER DEFAULT 0,
    duration_formatted TEXT DEFAULT '00:00',
    thumbnail_url TEXT,
    published_at TEXT,
    description TEXT,
    captions_available INTEGER DEFAULT 0,
    metadata_source TEXT DEFAULT 'oembed',
    embed_permitted INTEGER DEFAULT 1,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    source TEXT NOT NULL,
    language TEXT DEFAULT 'en',
    segments_json TEXT NOT NULL,
    chunks_json TEXT NOT NULL,
    created_at REAL NOT NULL,
    UNIQUE(video_id, user_id)
);

CREATE TABLE IF NOT EXISTS notes (
    note_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    video_id TEXT NOT NULL,
    video_title TEXT NOT NULL,
    channel TEXT,
    summary_type TEXT NOT NULL,
    content TEXT NOT NULL,
    chapters_json TEXT DEFAULT '[]',
    key_points_json TEXT DEFAULT '[]',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS history (
    history_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    video_id TEXT NOT NULL,
    action TEXT NOT NULL,
    details_json TEXT DEFAULT '{}',
    timestamp REAL NOT NULL
);
```
