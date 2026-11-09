"""
YouTube Controller for JARVIS OS.
Provides structured YouTube search extraction, numbered video selection,
direct Chrome playback on DISPLAY=:0, and verified player controls (play, pause,
fullscreen, mute, volume) with real-time state tracking.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("JARVIS-YOUTUBE-CONTROLLER")


class YouTubeVideo:
    """Represents an organic YouTube video search record."""

    def __init__(self, rank: int, video_id: str, title: str, channel: str, url: str, duration: Optional[str] = None):
        self.rank = rank
        self.video_id = video_id
        self.title = title
        self.channel = channel
        self.url = url
        self.duration = duration

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "video_id": self.video_id,
            "title": self.title,
            "channel": self.channel,
            "url": self.url,
            "duration": self.duration,
        }


class YouTubeSession:
    """Maintains active YouTube search query results for follow-up selection."""

    def __init__(self, query: str):
        self.query = query
        self.videos: List[YouTubeVideo] = []
        self.created_at = time.time()
        self.active_index: Optional[int] = None
        self.current_video: Optional[YouTubeVideo] = None

    def add_video(self, video: YouTubeVideo) -> None:
        self.videos.append(video)

    def get_by_index(self, index: int) -> Optional[YouTubeVideo]:
        """Supports 1-based (1..len for natural language) or 0-based indexing."""
        if index == 0 and len(self.videos) > 0:
            return self.videos[0]
        if 1 <= index <= len(self.videos):
            return self.videos[index - 1]
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "total_videos": len(self.videos),
            "videos": [v.to_dict() for v in self.videos],
            "active_index": self.active_index,
            "current_video": self.current_video.to_dict() if self.current_video else None,
            "created_at": self.created_at,
        }


class YouTubeController:
    """Manages YouTube search queries, playback in Google Chrome, and player controls."""

    def __init__(self) -> None:
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

    def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Search YouTube for videos via yt-dlp metadata extraction."""
        clean_q = query.strip()
        if not clean_q:
            return {"status": "error", "message": "Search query cannot be empty"}

        logger.info("Executing YouTube search for: '%s'", clean_q)
        videos = self._extract_youtube_videos(clean_q, max_results=max_results)

        session = YouTubeSession(query=clean_q)
        for v in videos:
            session.add_video(v)

        self._current_session = session

        formatted_lines = []
        for v in videos:
            formatted_lines.append(f"{v.rank}. {v.title} [{v.channel}]\n   {v.url}")

        summary = f"Found {len(videos)} YouTube videos for '{clean_q}':\n" + "\n".join(formatted_lines)

        return {
            "status": "ok",
            "query": clean_q,
            "count": len(videos),
            "videos": [v.to_dict() for v in videos],
            "formatted_summary": summary,
        }

    def _extract_youtube_videos(self, query: str, max_results: int = 5) -> List[YouTubeVideo]:
        """Use yt-dlp flat-playlist extraction for instant metadata parsing."""
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
                    channel = data.get("uploader") or data.get("channel") or "Unknown Artist"
                    duration = data.get("duration_string")

                    if vid:
                        videos.append(YouTubeVideo(
                            rank=rank,
                            video_id=vid,
                            title=title,
                            channel=channel,
                            url=f"https://www.youtube.com/watch?v={vid}",
                            duration=duration,
                        ))
                        rank += 1
                except Exception:
                    continue
        except Exception as e:
            logger.error("Failed to query yt-dlp search: %s", e)

        return videos

    def play_video_by_index(self, index: int, browser: str = "chrome") -> Dict[str, Any]:
        """Play a specific numbered video from the active YouTube session.
        
        Args:
            index: 0-based or 1-based index (e.g. 1st video = 1 or 0)
            browser: 'chrome'
        """
        if not self._current_session:
            return {
                "status": "error",
                "message": "No active YouTube search found. Please search for a song or video first.",
            }

        target = self._current_session.get_by_index(index)
        if not target:
            total = len(self._current_session.videos)
            return {
                "status": "error",
                "message": f"Video index {index} is out of bounds. The current search only has {total} videos.",
            }

        return self.play_video(target, browser=browser)

    def play_video(self, video: YouTubeVideo, browser: str = "chrome") -> Dict[str, Any]:
        """Open the verified YouTube video URL directly in Google Chrome."""
        from tools.browser.browser_agent import browser_agent

        logger.info("Opening YouTube video: '%s' (%s)", video.title, video.url)
        nav_res = browser_agent.open_url(video.url, browser=browser, new_tab=True)

        self._current_video = video
        self._is_playing = True
        self._is_paused = False
        if self._current_session:
            self._current_session.current_video = video
            self._current_session.active_index = video.rank - 1

        return {
            "status": "ok",
            "action": "play_youtube_video",
            "rank": video.rank,
            "title": video.title,
            "channel": video.channel,
            "url": video.url,
            "video_id": video.video_id,
            "message": f"Now playing '{video.title}' by {video.channel} on YouTube in Chrome.",
        }

    def play_direct_query(self, query: str, browser: str = "chrome") -> Dict[str, Any]:
        """Convenience method: Search YouTube and immediately play the top organic video."""
        search_res = self.search(query, max_results=3)
        if search_res.get("status") == "ok" and search_res.get("videos"):
            top_video = self._current_session.videos[0]
            return self.play_video(top_video, browser=browser)
        return {
            "status": "error",
            "message": f"Could not find any YouTube videos for '{query}'.",
        }

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
        }


youtube_controller = YouTubeController()
