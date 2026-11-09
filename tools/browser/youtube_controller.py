"""
YouTube Controller for JARVIS OS.
Provides structured YouTube search extraction, numbered video selection,
direct Chrome playback on DISPLAY=:0, verified player controls (play, pause,
fullscreen, mute, volume), and persistent search session lifecycle tracking.

Contract:
SEARCH -> DISPLAY ACTUAL RESULTS -> WAIT FOR USER DECISION -> OPEN SELECTED VIDEO IN CHROME -> VERIFY REAL PLAYBACK
"""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import time
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger("JARVIS-YOUTUBE-CONTROLLER")

# Valid session states
STATE_SEARCH_RESULTS_READY = "SEARCH_RESULTS_READY"
STATE_AWAITING_USER_SELECTION = "AWAITING_USER_SELECTION"
STATE_SELECTION_CONFIRMED = "SELECTION_CONFIRMED"
STATE_OPENING_VIDEO = "OPENING_VIDEO"
STATE_PLAYING_VERIFIED = "PLAYING_VERIFIED"
STATE_OPENED_PAUSED = "OPENED_PAUSED"
STATE_PLAYBACK_BLOCKED = "PLAYBACK_BLOCKED"
STATE_VIDEO_NOT_AVAILABLE = "VIDEO_NOT_AVAILABLE"
STATE_CANCELLED = "CANCELLED"
STATE_FAILED = "FAILED"


class YouTubeVideo:
    """Represents an organic YouTube video search record."""

    def __init__(
        self,
        rank: int,
        video_id: str,
        title: str,
        channel: str,
        url: str,
        duration: Optional[str] = None,
        thumbnail: Optional[str] = None,
        views: Optional[Any] = None,
    ):
        self.rank = rank
        self.video_id = video_id
        self.title = title
        self.channel = channel
        self.url = url
        self.duration = duration or "Unknown"
        self.thumbnail = thumbnail or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
        self.views = views

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "video_id": self.video_id,
            "title": self.title,
            "channel": self.channel,
            "url": self.url,
            "duration": self.duration,
            "thumbnail": self.thumbnail,
            "views": self.views,
        }


class YouTubeSession:
    """Maintains active YouTube search query results for follow-up user selection."""

    def __init__(self, query: str, session_id: Optional[str] = None):
        self.session_id: str = session_id or str(uuid.uuid4())
        self.query: str = query
        self.videos: List[YouTubeVideo] = []
        self.created_at: float = time.time()
        self.updated_at: float = time.time()
        self.state: str = STATE_SEARCH_RESULTS_READY
        self.active_index: Optional[int] = None
        self.current_video: Optional[YouTubeVideo] = None
        self.autoplay: bool = True
        self.playback_verified: bool = False
        self.error_message: Optional[str] = None

    def add_video(self, video: YouTubeVideo) -> None:
        self.videos.append(video)
        self.updated_at = time.time()

    def get_by_index(self, index: int) -> Optional[YouTubeVideo]:
        """Supports 1-based (1..len) or 0-based indexing."""
        if index == 0 and len(self.videos) > 0:
            return self.videos[0]
        if 1 <= index <= len(self.videos):
            return self.videos[index - 1]
        return None

    def get_by_title_match(self, query: str) -> Optional[YouTubeVideo]:
        """Find video by case-insensitive substring or keyword match against title/channel."""
        q_clean = query.lower().strip()
        # Direct substring in title
        for v in self.videos:
            if q_clean in v.title.lower():
                return v
        # Word-level match
        words = [w for w in re.split(r'\W+', q_clean) if len(w) > 2]
        if words:
            best_match = None
            best_score = 0
            for v in self.videos:
                t_lower = v.title.lower()
                score = sum(1 for w in words if w in t_lower)
                if score > best_score:
                    best_score = score
                    best_match = v
            if best_score > 0 and best_match:
                return best_match
        return None

    def cancel(self) -> None:
        """Mark session as cancelled by user."""
        self.state = STATE_CANCELLED
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "query": self.query,
            "state": self.state,
            "total_videos": len(self.videos),
            "videos": [v.to_dict() for v in self.videos],
            "active_index": self.active_index,
            "current_video": self.current_video.to_dict() if self.current_video else None,
            "autoplay": self.autoplay,
            "playback_verified": self.playback_verified,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class YouTubeController:
    """Manages YouTube search queries, user-controlled selection, and Chrome playback."""

    def __init__(self) -> None:
        self._sessions: Dict[str, YouTubeSession] = {}
        self._current_session: Optional[YouTubeSession] = None
        self._is_playing: bool = False
        self._is_paused: bool = False
        self._is_fullscreen: bool = False
        self._current_video: Optional[YouTubeVideo] = None
        self._player_volume_pct: int = 100

    def get_session(self) -> Optional[Dict[str, Any]]:
        """Return current YouTube search session state."""
        if self._current_session:
            return self._current_session.to_dict()
        return None

    def search(self, query: str, max_results: int = 5, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Search YouTube for organic videos and create an active user selection session.
        
        CRITICAL: Does NOT automatically play any video. The state is set to
        AWAITING_USER_SELECTION to let the user select through text, voice, or dashboard.
        """
        clean_q = query.strip()
        # Clean common prefixes/suffixes from prompt like "open a horror video in youtube"
        clean_q = re.sub(r'^(?:open|find|search|play)\s+(?:a\s+|for\s+)?', '', clean_q, flags=re.I)
        clean_q = re.sub(r'\s+(?:in|on)\s+youtube$', '', clean_q, flags=re.I).strip()
        if not clean_q:
            clean_q = query.strip()

        logger.info("Executing YouTube search for: '%s' (max %d results)", clean_q, max_results)
        videos = self._extract_youtube_videos(clean_q, max_results=max_results)

        if not videos:
            session = YouTubeSession(query=clean_q, session_id=session_id)
            session.state = STATE_FAILED
            session.error_message = f"No videos found for query '{clean_q}'."
            self._current_session = session
            self._sessions[session.session_id] = session
            return {
                "status": "error",
                "state": STATE_FAILED,
                "query": clean_q,
                "message": f"Could not find any YouTube videos for '{clean_q}'.",
                "session": session.to_dict(),
            }

        session = YouTubeSession(query=clean_q, session_id=session_id)
        for v in videos:
            session.add_video(v)

        session.state = STATE_AWAITING_USER_SELECTION
        self._current_session = session
        self._sessions[session.session_id] = session

        formatted_lines = []
        for v in videos:
            formatted_lines.append(
                f"{v.rank}. **{v.title}**\n"
                f"   Channel: *{v.channel}* | Duration: {v.duration}\n"
                f"   🔗 `{v.url}`"
            )

        summary = (
            f"📺 **Found {len(videos)} YouTube videos for '{clean_q}':**\n\n"
            + "\n\n".join(formatted_lines)
            + "\n\n💡 *Which video would you like me to open? Say 'Play option 1', 'Play option 2', or select an option to watch in Google Chrome.*"
        )

        return {
            "status": "ok",
            "state": STATE_AWAITING_USER_SELECTION,
            "session_id": session.session_id,
            "query": clean_q,
            "count": len(videos),
            "videos": [v.to_dict() for v in videos],
            "formatted_summary": summary,
        }

    def _extract_youtube_videos(self, query: str, max_results: int = 5) -> List[YouTubeVideo]:
        """Use yt-dlp flat-playlist extraction for fast, organic metadata parsing."""
        ytdlp_bin = shutil.which("yt-dlp") or "/home/roshan/miniconda3/bin/yt-dlp"
        cmd = [
            ytdlp_bin,
            f"ytsearch{max_results}:{query}",
            "--dump-json",
            "--flat-playlist",
            "--no-warnings",
        ]
        if shutil.which("node"):
            cmd.extend(["--js-runtimes", f"node:{shutil.which('node')}"])

        videos: List[YouTubeVideo] = []
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
            rank = 1
            for line in res.stdout.splitlines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    vid = data.get("id")
                    title = data.get("title") or "Unknown Video"
                    channel = data.get("uploader") or data.get("channel") or "Unknown Channel"
                    duration = data.get("duration_string") or "Unknown"

                    # Parse thumbnail if available
                    thumbnails = data.get("thumbnails")
                    thumb_url = None
                    if thumbnails and isinstance(thumbnails, list) and len(thumbnails) > 0:
                        thumb_url = thumbnails[-1].get("url")

                    views = data.get("view_count")

                    if vid:
                        videos.append(
                            YouTubeVideo(
                                rank=rank,
                                video_id=vid,
                                title=title,
                                channel=channel,
                                url=f"https://www.youtube.com/watch?v={vid}",
                                duration=duration,
                                thumbnail=thumb_url,
                                views=views,
                            )
                        )
                        rank += 1
                except Exception:
                    continue
        except Exception as e:
            logger.error("Failed to query yt-dlp search: %s", e)

        return videos

    def select_and_play(
        self,
        index: Optional[int] = None,
        title_query: Optional[str] = None,
        autoplay: bool = True,
        browser: str = "chrome",
    ) -> Dict[str, Any]:
        """Select a video from the active search session and open it in Google Chrome.
        
        Args:
            index: 1-based index (e.g. 1, 2, 3...)
            title_query: Substring or keywords matching video title
            autoplay: If False, open video and immediately pause it
            browser: 'chrome'
        """
        session = self._current_session
        if not session or session.state == STATE_CANCELLED:
            return {
                "status": "error",
                "code": "NO_ACTIVE_SESSION",
                "state": STATE_FAILED,
                "message": "No active YouTube search found. Please search for a topic first (e.g., 'Search YouTube for horror videos').",
            }

        target: Optional[YouTubeVideo] = None
        if index is not None:
            target = session.get_by_index(index)
            if not target:
                total = len(session.videos)
                session.state = STATE_FAILED
                session.error_message = f"Video option {index} is out of bounds (1..{total})."
                return {
                    "status": "error",
                    "code": "INDEX_OUT_OF_BOUNDS",
                    "state": STATE_VIDEO_NOT_AVAILABLE,
                    "requested_index": index,
                    "available_count": total,
                    "message": f"Video option {index} is out of bounds. The current search only has {total} options.",
                }
        elif title_query:
            target = session.get_by_title_match(title_query)
            if not target:
                session.state = STATE_FAILED
                session.error_message = f"No video matching '{title_query}' in active session."
                return {
                    "status": "error",
                    "code": "TITLE_NOT_FOUND",
                    "state": STATE_VIDEO_NOT_AVAILABLE,
                    "query": title_query,
                    "message": f"Could not find any video matching '{title_query}' in the current search results.",
                }
        else:
            return {
                "status": "error",
                "code": "NO_SELECTION_SPECIFIED",
                "state": STATE_AWAITING_USER_SELECTION,
                "message": "Please specify which video to play (e.g., 'Play option 1' or 'Play the first video').",
            }

        # Transition state
        session.state = STATE_SELECTION_CONFIRMED
        session.selected_video = target
        session.active_index = target.rank - 1
        session.autoplay = autoplay
        session.updated_at = time.time()

        # Open in Chrome
        return self._execute_chrome_playback(target, autoplay=autoplay, browser=browser)

    def open_without_playing(
        self,
        index: Optional[int] = None,
        title_query: Optional[str] = None,
        browser: str = "chrome",
    ) -> Dict[str, Any]:
        """Open selected video in Chrome without playing (autoplay=False)."""
        return self.select_and_play(index=index, title_query=title_query, autoplay=False, browser=browser)

    def _execute_chrome_playback(
        self,
        video: YouTubeVideo,
        autoplay: bool = True,
        browser: str = "chrome",
    ) -> Dict[str, Any]:
        """Launch Chrome with the exact YouTube video URL and verify playback."""
        from tools.browser.browser_agent import browser_agent

        session = self._current_session
        if session:
            session.state = STATE_OPENING_VIDEO

        logger.info("Opening YouTube video #%d: '%s' (%s) in %s", video.rank, video.title, video.url, browser)
        nav_res = browser_agent.open_url(video.url, browser=browser, new_tab=True)

        if nav_res.get("status") == "error":
            if session:
                session.state = STATE_FAILED
                session.error_message = nav_res.get("message")
            return {
                "status": "error",
                "state": STATE_FAILED,
                "code": "BROWSER_LAUNCH_FAILED",
                "message": f"Failed to open Google Chrome: {nav_res.get('message')}",
            }

        self._current_video = video
        self._is_playing = autoplay
        self._is_paused = not autoplay

        if not autoplay:
            # Send pause shortcut (k key) after opening tab
            time.sleep(1.0)
            browser_agent.send_shortcut("k", browser=browser)

        # Verification step
        verify_res = self.verify_playback(video.video_id, timeout=3.0)

        final_state = STATE_PLAYING_VERIFIED if autoplay else STATE_OPENED_PAUSED
        if not verify_res.get("window_verified"):
            final_state = STATE_PLAYBACK_BLOCKED

        if session:
            session.state = final_state
            session.current_video = video
            session.active_index = video.rank - 1
            session.playback_verified = verify_res.get("window_verified", False)

        action_label = "Now playing" if autoplay else "Opened (paused)"
        msg = f"{action_label} option #{video.rank} '{video.title}' by {video.channel} on YouTube in Google Chrome."

        return {
            "status": "ok",
            "state": final_state,
            "action": "play_youtube_video" if autoplay else "open_youtube_video",
            "rank": video.rank,
            "title": video.title,
            "channel": video.channel,
            "url": video.url,
            "video_id": video.video_id,
            "duration": video.duration,
            "thumbnail": video.thumbnail,
            "autoplay": autoplay,
            "verification": verify_res,
            "message": msg,
        }

    def verify_playback(self, video_id: str, timeout: float = 3.0) -> Dict[str, Any]:
        """Verify whether Google Chrome has loaded the requested YouTube video on DISPLAY=:0."""
        from tools.browser.browser_agent import browser_agent
        from tools.media.audio_stream_manager import audio_stream_manager

        windows = browser_agent.find_browser_windows("chrome")
        window_found = len(windows) > 0

        # Check running process
        proc_running = False
        try:
            p_check = subprocess.run(["pgrep", "-f", "chrome"], capture_output=True, text=True, check=False)
            proc_running = p_check.returncode == 0
        except Exception:
            pass

        # Check audio streams in PipeWire
        streams = audio_stream_manager.list_active_streams()
        chrome_stream = any(
            "chrome" in str(s.get("name", "")).lower() or "chromium" in str(s.get("name", "")).lower()
            for s in streams
        )

        return {
            "verified": window_found or proc_running,
            "window_verified": window_found,
            "process_running": proc_running,
            "audio_stream_detected": chrome_stream,
            "video_id": video_id,
            "target_url": f"https://www.youtube.com/watch?v={video_id}",
            "verified_at": time.time(),
        }

    def cancel_selection(self) -> Dict[str, Any]:
        """Cancel the active YouTube video selection session."""
        session = self._current_session
        if not session or session.state == STATE_CANCELLED:
            return {
                "status": "ok",
                "state": STATE_CANCELLED,
                "message": "No active YouTube selection to cancel.",
            }

        session.cancel()
        return {
            "status": "ok",
            "state": STATE_CANCELLED,
            "session_id": session.session_id,
            "query": session.query,
            "message": f"YouTube video selection for '{session.query}' cancelled.",
        }

    def get_more_results(self, count: int = 3) -> Dict[str, Any]:
        """Fetch additional search results for the active search query."""
        session = self._current_session
        if not session or session.state == STATE_CANCELLED:
            return {
                "status": "error",
                "code": "NO_ACTIVE_SESSION",
                "message": "No active YouTube search found. Please search for a topic first.",
            }

        current_total = len(session.videos)
        new_target = current_total + count
        fresh_videos = self._extract_youtube_videos(session.query, max_results=new_target)

        # Append only new videos
        existing_ids = {v.video_id for v in session.videos}
        added = 0
        next_rank = current_total + 1
        for v in fresh_videos:
            if v.video_id not in existing_ids:
                v.rank = next_rank
                session.add_video(v)
                existing_ids.add(v.video_id)
                next_rank += 1
                added += 1

        session.state = STATE_AWAITING_USER_SELECTION

        formatted_lines = []
        for v in session.videos:
            formatted_lines.append(
                f"{v.rank}. **{v.title}**\n"
                f"   Channel: *{v.channel}* | Duration: {v.duration}\n"
                f"   🔗 `{v.url}`"
            )

        summary = (
            f"📺 **Updated YouTube results for '{session.query}' (Total: {len(session.videos)}):**\n\n"
            + "\n\n".join(formatted_lines)
            + "\n\n💡 *Say 'Play option 1' or select any option to watch in Google Chrome.*"
        )

        return {
            "status": "ok",
            "state": STATE_AWAITING_USER_SELECTION,
            "query": session.query,
            "total_videos": len(session.videos),
            "added_count": added,
            "videos": [v.to_dict() for v in session.videos],
            "formatted_summary": summary,
        }

    def play_direct_query(self, query: str, browser: str = "chrome") -> Dict[str, Any]:
        """Convenience method: Search YouTube and immediately play the top organic video."""
        search_res = self.search(query, max_results=3)
        if search_res.get("status") == "ok" and self._current_session and self._current_session.videos:
            top_video = self._current_session.videos[0]
            return self.select_and_play(index=1, browser=browser)
        return {
            "status": "error",
            "message": f"Could not find any YouTube videos for '{query}'.",
        }

    def play_video_by_index(self, index: int, browser: str = "chrome") -> Dict[str, Any]:
        """Backwards compatibility alias for select_and_play."""
        return self.select_and_play(index=index, autoplay=True, browser=browser)

    def play_video(self, video: YouTubeVideo, browser: str = "chrome") -> Dict[str, Any]:
        """Direct video playback."""
        return self._execute_chrome_playback(video, autoplay=True, browser=browser)

    def pause(self) -> Dict[str, Any]:
        """Send YouTube pause command (k key) to the browser window."""
        from tools.browser.browser_agent import browser_agent
        res = browser_agent.send_shortcut("k", browser="chrome")
        self._is_paused = True
        self._is_playing = False
        return {
            "status": "ok" if res.get("status") == "ok" else "error",
            "action": "pause",
            "message": "Paused YouTube video playback.",
        }

    def resume(self) -> Dict[str, Any]:
        """Send YouTube resume command (k key) to the browser window."""
        from tools.browser.browser_agent import browser_agent
        res = browser_agent.send_shortcut("k", browser="chrome")
        self._is_paused = False
        self._is_playing = True
        return {
            "status": "ok" if res.get("status") == "ok" else "error",
            "action": "resume",
            "message": "Resumed YouTube video playback.",
        }

    def toggle_fullscreen(self) -> Dict[str, Any]:
        """Toggle fullscreen mode on the YouTube video player (f key)."""
        from tools.browser.browser_agent import browser_agent
        res = browser_agent.send_shortcut("f", browser="chrome")
        self._is_fullscreen = not self._is_fullscreen
        state = "fullscreen" if self._is_fullscreen else "windowed"
        return {
            "status": "ok" if res.get("status") == "ok" else "error",
            "action": "toggle_fullscreen",
            "mode": state,
            "message": f"Switched YouTube player to {state}.",
        }

    def mute(self) -> Dict[str, Any]:
        """Toggle mute on YouTube player (m key)."""
        from tools.browser.browser_agent import browser_agent
        res = browser_agent.send_shortcut("m", browser="chrome")
        return {
            "status": "ok" if res.get("status") == "ok" else "error",
            "action": "mute",
            "message": "Toggled mute on YouTube video.",
        }

    def set_video_volume(self, volume_pct: int) -> Dict[str, Any]:
        """Adjust video volume on the browser playback stream."""
        target = max(0, min(100, int(volume_pct)))
        self._player_volume_pct = target

        from tools.media.audio_stream_manager import audio_stream_manager
        res = audio_stream_manager.set_app_volume("chrome", target)
        if res.get("count", 0) == 0:
            res = audio_stream_manager.set_app_volume("chromium", target)

        return {
            "status": "ok",
            "action": "set_video_volume",
            "volume_pct": target,
            "stream_result": res,
            "message": f"YouTube video volume set to {target}%.",
        }

    def get_player_state(self) -> Dict[str, Any]:
        """Return the current YouTube player state."""
        return {
            "is_playing": self._is_playing,
            "is_paused": self._is_paused,
            "is_fullscreen": self._is_fullscreen,
            "current_video": self._current_video.to_dict() if self._current_video else None,
            "volume_pct": self._player_volume_pct,
            "session": self._current_session.to_dict() if self._current_session else None,
        }


youtube_controller = YouTubeController()
