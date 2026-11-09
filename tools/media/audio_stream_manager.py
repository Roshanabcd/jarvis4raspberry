"""
Audio Stream Manager for JARVIS OS.
Manages PipeWire audio streams, per-application volume levels, intelligent
audio ducking during speech synthesis, and master sink volume protection.
Prevents unintended master volume overrides and accidental media killing.
"""
from __future__ import annotations

import logging
import re
import subprocess
from typing import Any, Dict, List, Optional

logger = logging.getLogger("JARVIS-AUDIO-STREAM")


class AudioStreamManager:
    """Manages PipeWire audio streams and provides safe, separated volume control."""

    def __init__(self) -> None:
        self._ducked_streams: Dict[int, float] = {}

    def get_wpctl_status(self) -> str:
        """Run 'wpctl status' and return raw text output."""
        try:
            res = subprocess.run(
                ["wpctl", "status"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            return res.stdout
        except Exception as e:
            logger.error("Failed to run wpctl status: %s", e)
            return ""

    def list_active_streams(self) -> List[Dict[str, Any]]:
        """Parse active audio playback and capture streams from wpctl status."""
        status_text = self.get_wpctl_status()
        streams: List[Dict[str, Any]] = []
        if not status_text:
            return streams

        in_audio = False
        in_streams = False

        # Lines in Audio -> Streams section typically look like:
        #        95. pw-record
        #       110. FreeTube
        #             94. output_FR       > ReSpeaker Lite:playback_FR	[active]
        current_stream: Optional[Dict[str, Any]] = None

        for line in status_text.splitlines():
            # Section boundaries
            if "Audio" in line and not line.startswith(" "):
                in_audio = True
                continue
            elif in_audio and ("Video" in line or "Settings" in line) and not line.startswith(" "):
                in_audio = False
                in_streams = False
                break

            if in_audio:
                if "Streams:" in line:
                    in_streams = True
                    continue
                elif in_streams and line.strip().startswith(("Devices:", "Sinks:", "Sources:", "Filters:")):
                    in_streams = False
                    continue

                if in_streams:
                    # Match a stream root entry e.g. "       110. FreeTube"
                    stream_match = re.match(r"^\s*(\d+)\.\s+([A-Za-z0-9_\-\.\s]+?)\s*$", line)
                    if stream_match:
                        stream_id = int(stream_match.group(1))
                        name = stream_match.group(2).strip()
                        current_stream = {
                            "stream_id": stream_id,
                            "name": name,
                            "direction": "playback",  # refined below
                            "channels": [],
                            "active": False,
                            "volume": self.get_stream_volume(stream_id),
                        }
                        streams.append(current_stream)
                        continue

                    # Match channel routing lines e.g.:
                    # 94. output_FR > ReSpeaker Lite:playback_FR [active]
                    # 115. input_FL < ReSpeaker Lite:capture_FL [active]
                    if current_stream:
                        chan_match = re.search(r"(\d+)\.\s+([a-zA-Z0-9_]+)\s+([<>])\s+(.+?)(?:\[(active)\])?$", line)
                        if chan_match:
                            chan_id = int(chan_match.group(1))
                            chan_name = chan_match.group(2)
                            direction_symbol = chan_match.group(3)
                            target = chan_match.group(4).strip()
                            is_active = bool(chan_match.group(5))

                            if direction_symbol == "<":
                                current_stream["direction"] = "capture"
                            else:
                                current_stream["direction"] = "playback"

                            if is_active:
                                current_stream["active"] = True

                            current_stream["channels"].append({
                                "channel_id": chan_id,
                                "channel_name": chan_name,
                                "target": target,
                                "active": is_active,
                            })

        return streams

    def get_stream_volume(self, stream_id: int) -> float:
        """Get volume of a specific PipeWire stream (0.0 to 1.0+)."""
        try:
            res = subprocess.run(
                ["wpctl", "get-volume", str(stream_id)],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if res.returncode == 0:
                # Output format: "Volume: 0.85" or "Volume: 1.00 [MUTED]"
                m = re.search(r"Volume:\s+([0-9\.]+)", res.stdout)
                if m:
                    return float(m.group(1))
        except Exception as e:
            logger.debug("Failed to get volume for stream %s: %s", stream_id, e)
        return 1.0

    def set_stream_volume(self, stream_id: int, volume_fraction: float) -> bool:
        """Set volume of a specific stream without modifying master sink.
        
        Args:
            stream_id: PipeWire stream node id
            volume_fraction: 0.0 to 1.0 (or up to 1.5 for boost)
        """
        vol = max(0.0, min(1.5, float(volume_fraction)))
        vol_str = f"{vol:.2f}"
        try:
            res = subprocess.run(
                ["wpctl", "set-volume", str(stream_id), vol_str],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            return res.returncode == 0
        except Exception as e:
            logger.error("Failed to set stream %s volume to %s: %s", stream_id, vol_str, e)
            return False

    def set_app_volume(self, app_name: str, volume_percent: int) -> Dict[str, Any]:
        """Adjust stream volume for all active streams matching app_name."""
        vol_frac = max(0.0, min(100.0, float(volume_percent))) / 100.0
        streams = self.list_active_streams()
        target_name = app_name.lower().strip()
        matched = []

        for s in streams:
            if s["direction"] == "playback" and target_name in s["name"].lower():
                ok = self.set_stream_volume(s["stream_id"], vol_frac)
                matched.append({
                    "stream_id": s["stream_id"],
                    "name": s["name"],
                    "new_volume": vol_frac,
                    "success": ok,
                })

        return {
            "app": app_name,
            "target_volume_pct": volume_percent,
            "modified_streams": matched,
            "count": len(matched),
        }

    def get_master_sink_volume(self) -> Dict[str, Any]:
        """Get the hardware master sink volume and mute status."""
        try:
            res = subprocess.run(
                ["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if res.returncode == 0:
                m = re.search(r"Volume:\s+([0-9\.]+)", res.stdout)
                vol = float(m.group(1)) if m else 1.0
                muted = "[MUTED]" in res.stdout
                return {"volume": vol, "volume_pct": int(round(vol * 100)), "muted": muted}
        except Exception as e:
            logger.error("Failed to get master sink volume: %s", e)
        return {"volume": 1.0, "volume_pct": 100, "muted": False}

    def set_master_sink_volume(self, volume_percent: int) -> Dict[str, Any]:
        """Explicitly set hardware master sink volume.
        
        ONLY call this when user explicitly requests 'system volume' or 'master volume'.
        """
        vol_frac = max(0.0, min(100.0, float(volume_percent))) / 100.0
        vol_str = f"{vol_frac:.2f}"
        try:
            res = subprocess.run(
                ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", vol_str],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            return {
                "success": res.returncode == 0,
                "target_volume_pct": volume_percent,
                "volume_fraction": vol_frac,
            }
        except Exception as e:
            logger.error("Failed to set master sink volume to %s: %s", vol_str, e)
            return {"success": False, "error": str(e)}

    def duck_active_streams(self, duck_fraction: float = 0.20) -> Dict[int, float]:
        """Duck active media streams (FreeTube, Spotify, Chrome) during speech output.
        
        Saves original volumes in self._ducked_streams so they can be restored.
        """
        streams = self.list_active_streams()
        ducked: Dict[int, float] = {}

        for s in streams:
            # Only duck playback streams from user media apps, not JARVIS or system monitors
            if s["direction"] == "playback" and s["active"]:
                app_lower = s["name"].lower()
                if any(media_app in app_lower for media_app in ["freetube", "chrome", "chromium", "firefox", "vlc", "spotify", "music"]):
                    orig_vol = s["volume"]
                    duck_target = min(orig_vol, duck_fraction)
                    if self.set_stream_volume(s["stream_id"], duck_target):
                        ducked[s["stream_id"]] = orig_vol
                        self._ducked_streams[s["stream_id"]] = orig_vol
                        logger.info(
                            "Ducked stream %s (%s) from %.2f to %.2f",
                            s["stream_id"], s["name"], orig_vol, duck_target
                        )

        return ducked

    def restore_active_streams(self) -> Dict[int, float]:
        """Restore all previously ducked streams back to their original volumes."""
        restored: Dict[int, float] = {}
        for stream_id, orig_vol in list(self._ducked_streams.items()):
            if self.set_stream_volume(stream_id, orig_vol):
                restored[stream_id] = orig_vol
                logger.info("Restored stream %s to %.2f", stream_id, orig_vol)

        self._ducked_streams.clear()
        return restored


audio_stream_manager = AudioStreamManager()
