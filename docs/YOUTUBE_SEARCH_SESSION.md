# JARVIS OS — YouTube Search Session and Lifecycle Management

## 1. Overview

The `YouTubeSession` engine maintains search context across multi-turn interactions. It ensures that when a user asks for "option 1", "option 2", or "the first horror movie in YouTube", JARVIS resolves the request strictly against the user's active search session rather than performing a disconnected query.

---

## 2. Session Data Contract

### 2.1 `YouTubeVideo` Structure
```python
class YouTubeVideo:
    rank: int                      # 1-based order in search results (1..N)
    video_id: str                  # 11-character YouTube video ID
    title: str                     # Organic title from YouTube metadata
    channel: str                   # Channel or uploader name
    url: str                       # https://www.youtube.com/watch?v={video_id}
    duration: str                  # Formatted duration string (e.g. "15:33")
    thumbnail: str                 # High-resolution thumbnail image URL
    views: Optional[int]           # View count
```

### 2.2 `YouTubeSession` Structure
```python
class YouTubeSession:
    session_id: str                # UUID v4 string
    query: str                     # Search query string (e.g. "horror video")
    state: str                     # Current lifecycle state
    created_at: float              # Unix timestamp
    updated_at: float              # Unix timestamp of last state transition
    videos: List[YouTubeVideo]     # Ordered list of retrieved videos
    selected_video: Optional[YouTubeVideo] # Currently selected video
    active_index: Optional[int]    # 0-based index of selected video
    autoplay: bool                 # True for direct play; False for "without playing"
    playback_verified: bool        # True if window & display verification succeeded
    error_message: Optional[str]   # Diagnostic message on failure
```

---

## 3. Lifecycle State Machine

The session transitions through the following honest states:

| State | Trigger | Description |
|---|---|---|
| `SEARCH_RESULTS_READY` | yt-dlp metadata extraction complete | 5 organic search results parsed into memory |
| `AWAITING_USER_SELECTION` | Search results presented to user | Waiting for user choice via voice, text, or UI. **No video is played.** |
| `SELECTION_CONFIRMED` | User specifies option or title | Valid video index identified and bound |
| `OPENING_VIDEO` | Chrome launch command sent | Google Chrome launching tab on `DISPLAY=:0` |
| `PLAYING_VERIFIED` | Chrome window and process verified | Playback successfully confirmed running |
| `OPENED_PAUSED` | User specified "without playing" | Video opened in Chrome and immediately paused |
| `PLAYBACK_BLOCKED` | Chrome failed to open or window lost | Honest reporting of display/window issue |
| `VIDEO_NOT_AVAILABLE` | Out-of-bounds index requested | Honest error informing available option count |
| `CANCELLED` | User says "Cancel selection" | Session terminated; follow-up selection disabled |
| `FAILED` | Query returned 0 results | User prompted to try a different query |

---

## 4. Multi-Turn Decision Flow

```
[User Turn 1] "Open a horror video in YouTube"
       │
       ▼
   Extract 5 organic videos via yt-dlp
       │
       ▼
   Initialize YouTubeSession(query="horror video")
       │
       ▼
   Set State: AWAITING_USER_SELECTION
       │
       ▼
   Respond with numbered options (1..5) + prompt:
   "Which video would you like me to open? Say 'Play option 1', 'Play option 2'..."
       │
       ▼
[User Turn 2] "Play the first horror movie in YouTube"
       │
       ▼
   LocalEngine matches: youtube_play_index (index=1)
       │
       ▼
   Session resolves: get_by_index(1) -> Video #1: "SCARIEST VIDEOS ON THE INTERNET"
       │
       ▼
   Launch Chrome: https://www.youtube.com/watch?v=hjEHVCgBBV8 on DISPLAY=:0
       │
       ▼
   Verify Playback -> Set State: PLAYING_VERIFIED
       │
       ▼
   Respond: "▶️ Now playing option #1 on YouTube in Google Chrome: SCARIEST VIDEOS ON THE INTERNET"
```

---

## 5. Session Operations

### 5.1 Numbered Index Lookup
```python
def get_by_index(self, index: int) -> Optional[YouTubeVideo]:
    if index == 0 and len(self.videos) > 0:
        return self.videos[0]
    if 1 <= index <= len(self.videos):
        return self.videos[index - 1]
    return None
```

### 5.2 Fuzzy Title Match
```python
def get_by_title_match(self, query: str) -> Optional[YouTubeVideo]:
    # 1. Exact substring match
    for v in self.videos:
        if query.lower() in v.title.lower():
            return v
    # 2. Token overlap score
    # Returns the best matching video if score > 0
```

### 5.3 Fetching More Results
When user requests "Show 3 more results", `youtube_controller.get_more_results(count=3)` fetches the next 3 results from YouTube, appends them as ranks 6, 7, and 8, and re-presents the updated list while remaining in state `AWAITING_USER_SELECTION`.
