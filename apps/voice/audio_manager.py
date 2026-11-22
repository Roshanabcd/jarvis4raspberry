"""Audio Manager for JARVIS OS.

Handles detection and selection of audio recording devices, with support for
hardware auto-detection (ALSA arecord) and simulation mode fallback.
"""

import logging
import re
import subprocess
from typing import Any, Dict, List, Optional

from config.config_manager import config

logger = logging.getLogger("JARVIS-AUDIO")


class AudioManager:
    """Manages audio input hardware detection and device selection."""

    def __init__(self, simulation_mode: Optional[bool] = None):
        """Initialize the audio manager.

        Args:
            simulation_mode: Explicit flag to force simulation mode. If None,
                checks voice-specific config or defaults to False (Real Hardware Mode).
        """
        if simulation_mode is not None:
            self.simulation_mode = simulation_mode
        else:
            voice_cfg = config.get("voice", {}) if hasattr(config, "get") else {}
            if "simulation_mode" in voice_cfg:
                self.simulation_mode = bool(voice_cfg["simulation_mode"])
            else:
                self.simulation_mode = False

        self.selected_device: Optional[Dict[str, Any]] = None
        self.selected_playback_device: Optional[Dict[str, Any]] = None
        self.current_volume: float = 0.65
        logger.info(
            "AudioManager initialized (simulation_mode=%s)", self.simulation_mode
        )

    def is_simulation(self) -> bool:
        """Check whether simulation mode is active.

        Returns:
            bool: True if in simulation mode.
        """
        return self.simulation_mode

    def detect_devices(self) -> List[Dict[str, Any]]:
        """Scan for audio input devices using ALSA 'arecord -l'.

        Returns:
            List[Dict[str, Any]]: List of detected devices, each represented as
                {'card': int, 'device': int, 'name': str}.
        """
        if self.is_simulation():
            logger.debug("Simulation mode active: returning simulated input device")
            return [{"card": 0, "device": 0, "name": "Simulated"}]

        devices: List[Dict[str, Any]] = []
        try:
            result = subprocess.run(
                ["arecord", "-l"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            if result.returncode != 0:
                logger.warning(
                    "arecord -l returned non-zero code (%d): %s",
                    result.returncode,
                    result.stderr.strip(),
                )
                return [{"card": 0, "device": 0, "name": "Simulated"}]

            output = result.stdout
            # Pattern matching ALSA arecord -l lines, e.g.:
            # card 1: ReSpeaker [Seeed ReSpeaker Lite], device 0: USB Audio [USB Audio]
            pattern = re.compile(
                r"^card\s+(\d+):\s*([^,]+),\s*device\s+(\d+):\s*(.+)$",
                re.MULTILINE,
            )

            for match in pattern.finditer(output):
                card_id = int(match.group(1))
                card_name = match.group(2).strip()
                device_id = int(match.group(3))
                device_name = match.group(4).strip()

                full_name = f"{card_name} - {device_name}"
                devices.append(
                    {
                        "card": card_id,
                        "device": device_id,
                        "name": full_name,
                    }
                )

            logger.info("Detected %d audio input devices via arecord", len(devices))
            if not devices:
                logger.warning("No audio devices detected via arecord, using simulated")
                return [{"card": 0, "device": 0, "name": "Simulated"}]

            return devices

        except FileNotFoundError:
            logger.warning("arecord binary not found on system; falling back to simulation")
            return [{"card": 0, "device": 0, "name": "Simulated"}]
        except subprocess.TimeoutExpired:
            logger.error("arecord -l command timed out; falling back to simulation")
            return [{"card": 0, "device": 0, "name": "Simulated"}]
        except Exception as exc:
            logger.error("Error executing arecord -l: %s; falling back to simulation", exc)
            return [{"card": 0, "device": 0, "name": "Simulated"}]

    def select_best_device(self) -> Dict[str, Any]:
        """Select the optimal audio input device.

        Picks 'ReSpeaker Lite' if present, otherwise returns the first available device.
        In simulation mode, returns {'card': 0, 'device': 0, 'name': 'Simulated'}.

        Returns:
            Dict[str, Any]: Selected device with 'card', 'device', and 'name'.
        """
        if self.is_simulation():
            logger.info("Simulation mode: selected simulated device")
            self.selected_device = {"card": 0, "device": 0, "name": "Simulated"}
            return self.selected_device

        devices = self.detect_devices()
        if not devices:
            self.selected_device = {"card": 0, "device": 0, "name": "Simulated"}
            return self.selected_device

        # Prefer ReSpeaker Lite (or generic ReSpeaker)
        for dev in devices:
            name_lower = dev["name"].lower()
            if "respeaker lite" in name_lower or "respeaker" in name_lower:
                logger.info("Selected preferred ReSpeaker device: %s", dev)
                self.selected_device = dev
                return dev

        # Fallback to first available
        best = devices[0]
        logger.info("Selected first available audio device: %s", best)
        self.selected_device = best
        return best

    def is_microphone_available(self) -> bool:
        """Verify whether physical microphone hardware is actually connected and operable."""
        devices = self.detect_devices()
        return any(d.get("name") != "Simulated" for d in devices)

    def detect_playback_devices(self) -> List[Dict[str, Any]]:
        """Scan for audio output/playback devices using ALSA 'aplay -l'.

        Returns:
            List[Dict[str, Any]]: List of playback devices.
        """
        if self.is_simulation():
            return [{"card": 0, "device": 0, "name": "Simulated"}]

        devices: List[Dict[str, Any]] = []
        try:
            result = subprocess.run(
                ["aplay", "-l"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            if result.returncode != 0:
                return [{"card": 0, "device": 0, "name": "Simulated"}]

            pattern = re.compile(
                r"^card\s+(\d+):\s*([^,]+),\s*device\s+(\d+):\s*(.+)$",
                re.MULTILINE,
            )
            for match in pattern.finditer(result.stdout):
                card_id = int(match.group(1))
                card_name = match.group(2).strip()
                device_id = int(match.group(3))
                device_name = match.group(4).strip()
                devices.append({
                    "card": card_id,
                    "device": device_id,
                    "name": f"{card_name} - {device_name}",
                })
            return devices or [{"card": 0, "device": 0, "name": "Simulated"}]
        except Exception as exc:
            logger.warning("Error executing aplay -l: %s; falling back to simulation", exc)
            return [{"card": 0, "device": 0, "name": "Simulated"}]

    def select_best_playback_device(self) -> Dict[str, Any]:
        """Select preferred output speaker (user selection, ReSpeaker Lite, or first available)."""
        if self.selected_playback_device:
            return self.selected_playback_device
        devices = self.detect_playback_devices()
        for dev in devices:
            if "respeaker" in dev["name"].lower():
                return dev
        return devices[0] if devices else {"card": 0, "device": 0, "name": "Simulated"}

    def set_playback_device(self, card: int, device: int, name: Optional[str] = None) -> Dict[str, Any]:
        """Set user-selected audio playback device and update PipeWire default sink if found."""
        dev = {"card": card, "device": device, "name": name or f"Card {card} Device {device}"}
        self.selected_playback_device = dev
        try:
            proc = subprocess.run(["wpctl", "status"], capture_output=True, text=True, timeout=2)
            if proc.returncode == 0 and name:
                in_sinks = False
                for line in proc.stdout.splitlines():
                    if "Sinks:" in line:
                        in_sinks = True
                        continue
                    if in_sinks and "Sources:" in line:
                        break
                    if in_sinks and any(token.lower() in line.lower() for token in name.lower().split() if len(token) > 2):
                        m = re.search(r"(\d+)\.", line)
                        if m:
                            sink_id = m.group(1)
                            subprocess.run(["wpctl", "set-default", sink_id], timeout=2)
                            break
        except Exception as exc:
            logger.debug("Failed setting wpctl default sink: %s", exc)
        return dev

    def get_volume(self) -> float:
        """Read system output volume (0.0 - 1.5)."""
        try:
            res = subprocess.run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                m = re.search(r"Volume:\s*([0-9\.]+)", res.stdout)
                if m:
                    self.current_volume = float(m.group(1))
                    return self.current_volume
        except Exception:
            pass
        return self.current_volume

    def set_volume(self, volume: float) -> float:
        """Set system output volume (0.0 - 1.5)."""
        vol = max(0.0, min(1.5, float(volume)))
        try:
            subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{vol:.2f}"], timeout=2)
            self.current_volume = vol
        except Exception as exc:
            logger.warning("Failed setting volume via wpctl: %s", exc)
        return self.current_volume

    def get_device_alsa_identifier(self, device: Optional[Dict[str, Any]] = None, plug: bool = False) -> str:
        """Format an ALSA device string like 'hw:1,0' or 'plughw:1,0' for arecord/aplay.

        Args:
            device: Optional device dict. If None, uses selected_device.
            plug: If True, uses 'plughw:' prefix for automatic rate and format conversion.

        Returns:
            str: ALSA hardware identifier (e.g. 'hw:1,0', 'plughw:1,0' or 'default').
        """
        dev = device or self.selected_device
        if not dev or dev.get("name") == "Simulated":
            return "default"
        prefix = "plughw" if plug else "hw"
        return f"{prefix}:{dev.get('card', 0)},{dev.get('device', 0)}"

    def get_record_alsa_identifier(self, device: Optional[Dict[str, Any]] = None) -> str:
        """Format preferred recording identifier with plughw format conversion."""
        return self.get_device_alsa_identifier(device, plug=True)
