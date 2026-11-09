"""Media Player and Music Playback Manager for JARVIS OS.

Supports:
1. Local audio playback from ~/Music, ~/Downloads, /home/roshan, and project directories.
2. Online song streaming and extraction via yt-dlp.
3. Asynchronous non-blocking playback using cvlc, ffplay, or pw-play.
4. Volume adjustments and controls via PipeWire (wpctl) / ALSA.
5. Media controls: play, stop, pause, resume, status.
"""

from __future__ import annotations

import glob
import logging
import os
import shutil
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("JARVIS.MediaPlayer")

AUDIO_EXTENSIONS = (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".mpeg", ".aac", ".opus")


class MediaPlayer:
    """Manages audio and music playback on Raspberry Pi hardware."""

    _instance: Optional[MediaPlayer] = None

    def __new__(cls) -> MediaPlayer:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_player()
        return cls._instance

    def _init_player(self) -> None:
        self._current_process: Optional[subprocess.Popen] = None
        self._current_track: Optional[str] = None
        self._current_source: Optional[str] = None
        self._is_paused: bool = False
        self._lock = threading.RLock()
        self._cache_dir = "/tmp/jarvis_media"
        os.makedirs(self._cache_dir, exist_ok=True)

    def find_local_audio(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search local directories for audio files matching query."""
        search_dirs = [
            os.path.expanduser("~/Music"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data"),
        ]

        clean_query = query.lower().strip() if query else ""
        results = []
        seen_paths = set()

        for sdir in search_dirs:
            if not os.path.exists(sdir):
                continue
            for root, dirs, files in os.walk(sdir):
                # Don't recurse into hidden or heavy directories
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "venv", ".cache", "__pycache__")]
                for fname in files:
                    ext = os.path.splitext(fname)[1].lower()
                    if ext in AUDIO_EXTENSIONS:
                        fpath = os.path.join(root, fname)
                        if fpath in seen_paths:
                            continue
                        seen_paths.add(fpath)

                        score = 0
                        fname_lower = fname.lower()
                        if not clean_query:
                            score = 1
                        elif clean_query == fname_lower:
                            score = 100
                        elif clean_query in fname_lower:
                            score = 50
                        else:
                            # Substring or word match
                            words = clean_query.split()
                            if all(w in fname_lower for w in words):
                                score = 30

                        if score > 0:
                            results.append({
                                "name": fname,
                                "path": fpath,
                                "size": os.path.getsize(fpath),
                                "score": score,
                                "source": "local",
                            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def play(self, query: Optional[str] = None) -> Dict[str, Any]:
        """Play a local audio file or stream an online song."""
        with self._lock:
            self.stop()

            # 1. Check local audio files first
            local_matches = self.find_local_audio(query)
            if local_matches:
                target = local_matches[0]
                success, msg = self._start_playback(target["path"], is_local=True)
                if success:
                    self._current_track = target["name"]
                    self._current_source = target["path"]
                    return {
                        "status": "playing",
                        "title": target["name"],
                        "source": "local",
                        "path": target["path"],
                        "message": f"Playing '{target['name']}' from local storage.",
                    }

            # 2. If no query was given and no local files found
            if not query or not query.strip():
                return {
                    "status": "error",
                    "message": "No audio files found in ~/Music or ~/Downloads. Please specify a song name to play.",
                }

            # 3. Search and stream via yt-dlp
            logger.info("Local audio not found for '%s'. Searching online via yt-dlp...", query)
            stream_info = self._fetch_online_stream(query.strip())
            if not stream_info:
                return {
                    "status": "not_found",
                    "message": f"Could not find or stream audio for '{query}'.",
                }

            play_target = stream_info.get("stream_url") or stream_info.get("file_path")
            if not play_target:
                return {
                    "status": "error",
                    "message": f"No playable stream returned for '{query}'.",
                }

            success, msg = self._start_playback(play_target, is_local=bool(stream_info.get("file_path")))
            if success:
                self._current_track = stream_info.get("title", query)
                self._current_source = play_target
                return {
                    "status": "playing",
                    "title": stream_info.get("title", query),
                    "source": "online_stream",
                    "duration_s": stream_info.get("duration", 0),
                    "message": f"Now streaming '{stream_info.get('title', query)}'.",
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to start player: {msg}",
                }

    def _fetch_online_stream(self, query: str) -> Optional[Dict[str, Any]]:
        """Use yt-dlp to find best audio stream or download temporary audio."""
        ytdlp_bin = shutil.which("yt-dlp") or "/home/roshan/miniconda3/bin/yt-dlp"
        if not os.path.exists(ytdlp_bin):
            logger.warning("yt-dlp binary not found.")
            return None

        # Build yt-dlp command to extract metadata and direct audio stream URL
        cmd = [
            ytdlp_bin,
            f"ytsearch1:{query}",
            "--get-title",
            "--get-url",
            "-f", "bestaudio[ext=m4a]/bestaudio/best",
            "--no-playlist",
            "--no-check-certificates",
        ]
        if shutil.which("node"):
            cmd.extend(["--js-runtimes", f"node:{shutil.which('node')}"])

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
            lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
            if res.returncode == 0 and len(lines) >= 2:
                title = lines[0]
                stream_url = lines[1]
                return {
                    "title": title,
                    "stream_url": stream_url,
                }
            elif res.returncode == 0 and len(lines) == 1:
                return {
                    "title": query,
                    "stream_url": lines[0],
                }
        except subprocess.TimeoutExpired:
            logger.warning("yt-dlp stream fetch timed out for '%s'.", query)
        except Exception as e:
            logger.error("Error fetching online stream: %s", e)

        # Fallback: Download top 2-minute audio file directly
        try:
            out_template = os.path.join(self._cache_dir, "%(id)s.%(ext)s")
            dl_cmd = [
                ytdlp_bin,
                f"ytsearch1:{query}",
                "-f", "bestaudio[ext=m4a]/bestaudio",
                "-o", out_template,
                "--max-filesize", "20M",
                "--no-playlist",
            ]
            if shutil.which("node"):
                dl_cmd.extend(["--js-runtimes", f"node:{shutil.which('node')}"])

            dl_res = subprocess.run(dl_cmd, capture_output=True, text=True, timeout=18)
            if dl_res.returncode == 0:
                # Find downloaded file
                cached_files = glob.glob(os.path.join(self._cache_dir, "*"))
                if cached_files:
                    cached_files.sort(key=os.path.getmtime, reverse=True)
                    return {
                        "title": query,
                        "file_path": cached_files[0],
                    }
        except Exception as e:
            logger.error("Download fallback failed: %s", e)

        return None

    def _start_playback(self, path_or_url: str, is_local: bool = True) -> tuple[bool, str]:
        """Launch background audio player process."""
        # Preference: cvlc -> ffplay -> pw-play
        player_bin = None
        cmd = []

        if shutil.which("cvlc"):
            player_bin = shutil.which("cvlc")
            cmd = [player_bin, "--no-video", "--play-and-exit", "--quiet", path_or_url]
        elif shutil.which("ffplay"):
            player_bin = shutil.which("ffplay")
            cmd = [player_bin, "-nodisp", "-autoexit", "-loglevel", "quiet", path_or_url]
        elif is_local and shutil.which("pw-play"):
            player_bin = shutil.which("pw-play")
            cmd = [player_bin, path_or_url]
        elif is_local and shutil.which("aplay") and path_or_url.endswith(".wav"):
            player_bin = shutil.which("aplay")
            cmd = [player_bin, "-q", path_or_url]

        if not cmd:
            return False, "No audio player binary available (cvlc, ffplay, pw-play not found)."

        try:
            self._current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._is_paused = False
            logger.info("Started audio playback with PID %d: %s", self._current_process.pid, path_or_url)
            return True, "Playback started"
        except Exception as e:
            logger.error("Failed to launch player: %s", e)
            return False, str(e)

    def stop(self) -> Dict[str, Any]:
        """Halt any active music or song playback."""
        track = self._current_track or "audio"
        with self._lock:
            if self._current_process:
                try:
                    if self._current_process.poll() is None:
                        self._current_process.terminate()
                        self._current_process.wait(timeout=1.0)
                except Exception:
                    try:
                        self._current_process.kill()
                    except Exception:
                        pass
                self._current_process = None

            self._current_track = None
            self._current_source = None
            self._is_paused = False

        return {"status": "stopped", "message": f"Stopped playback of {track}."}

    def pause(self) -> Dict[str, Any]:
        """Pause playback using process signals."""
        with self._lock:
            if self._current_process and self._current_process.poll() is None:
                try:
                    import signal
                    os.kill(self._current_process.pid, signal.SIGSTOP)
                    self._is_paused = True
                    return {"status": "paused", "message": f"Paused '{self._current_track}'."}
                except Exception as e:
                    return {"status": "error", "message": f"Could not pause: {e}"}
        return {"status": "idle", "message": "No audio currently playing."}

    def resume(self) -> Dict[str, Any]:
        """Resume paused playback."""
        with self._lock:
            if self._current_process and self._current_process.poll() is None and self._is_paused:
                try:
                    import signal
                    os.kill(self._current_process.pid, signal.SIGCONT)
                    self._is_paused = False
                    return {"status": "resumed", "message": f"Resumed '{self._current_track}'."}
                except Exception as e:
                    return {"status": "error", "message": f"Could not resume: {e}"}
        return {"status": "idle", "message": "No paused playback to resume."}

    def is_playing(self) -> bool:
        """Check if audio is actively playing."""
        with self._lock:
            if self._current_process and self._current_process.poll() is None and not self._is_paused:
                return True
            return False

    def status(self) -> Dict[str, Any]:
        """Return current player state."""
        playing = self.is_playing()
        state = "playing" if playing else ("paused" if self._is_paused else "idle")
        return {
            "status": state,
            "is_playing": playing,
            "is_paused": self._is_paused,
            "track": self._current_track if (playing or self._is_paused) else None,
            "source": self._current_source if (playing or self._is_paused) else None,
        }

    def set_volume(self, level_pct: int) -> Dict[str, Any]:
        """Set output volume level between 0 and 100."""
        target = max(0, min(100, int(level_pct)))
        fraction = target / 100.0

        if shutil.which("wpctl"):
            try:
                subprocess.run(
                    ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{fraction:.2f}"],
                    capture_output=True,
                    timeout=3
                )
                return {"status": "ok", "volume_pct": target, "message": f"Volume set to {target}%"}
            except Exception as e:
                logger.warning("wpctl set-volume failed: %s", e)

        if shutil.which("pactl"):
            try:
                subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{target}%"], timeout=3)
                return {"status": "ok", "volume_pct": target, "message": f"Volume set to {target}%"}
            except Exception:
                pass

        if shutil.which("amixer"):
            try:
                subprocess.run(["amixer", "set", "Master", f"{target}%"], timeout=3)
                return {"status": "ok", "volume_pct": target, "message": f"Volume set to {target}%"}
            except Exception:
                pass

        return {"status": "error", "message": "Could not adjust system volume."}

    def adjust_volume(self, delta_pct: int) -> Dict[str, Any]:
        """Adjust volume relative to current level."""
        current = 100
        if shutil.which("wpctl"):
            try:
                res = subprocess.run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"], capture_output=True, text=True, timeout=2)
                for part in res.stdout.split():
                    try:
                        current = int(float(part) * 100)
                        break
                    except ValueError:
                        continue
            except Exception:
                pass

        new_vol = max(0, min(100, current + delta_pct))
        return self.set_volume(new_vol)


# Global singleton instance
media_player = MediaPlayer()

def get_media_player() -> MediaPlayer:
    return media_player
