"""
Theme Customization Manager for JARVIS OS.
Manages dashboard visual themes, CSS variable overrides, natural-language
theme commands, and persistent storage in data/theme_config.json.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, Optional

logger = logging.getLogger("JARVIS-THEME-MANAGER")

DEFAULT_THEME: Dict[str, str] = {
    "name": "jarvis-cyan",
    "bg_primary": "#030816",
    "bg_secondary": "#081226",
    "bg_card": "rgba(9, 21, 44, 0.75)",
    "color_accent": "#00f3ff",
    "color_accent_hover": "#00c4cc",
    "glow_accent": "rgba(0, 243, 255, 0.4)",
    "text_primary": "#e2f1ff",
    "text_secondary": "#8ba3c7",
    "border_color": "rgba(0, 243, 255, 0.25)",
}

COLOR_PRESETS: Dict[str, Dict[str, str]] = {
    "cyan": {
        "color_accent": "#00f3ff",
        "color_accent_hover": "#00c4cc",
        "glow_accent": "rgba(0, 243, 255, 0.4)",
        "border_color": "rgba(0, 243, 255, 0.25)",
    },
    "green": {
        "color_accent": "#00ff88",
        "color_accent_hover": "#00cc6a",
        "glow_accent": "rgba(0, 255, 136, 0.4)",
        "border_color": "rgba(0, 255, 136, 0.25)",
    },
    "purple": {
        "color_accent": "#b847ff",
        "color_accent_hover": "#9420dd",
        "glow_accent": "rgba(184, 71, 255, 0.4)",
        "border_color": "rgba(184, 71, 255, 0.25)",
    },
    "gold": {
        "color_accent": "#ffcc00",
        "color_accent_hover": "#cca300",
        "glow_accent": "rgba(255, 204, 0, 0.4)",
        "border_color": "rgba(255, 204, 0, 0.25)",
    },
    "red": {
        "color_accent": "#ff3355",
        "color_accent_hover": "#cc1133",
        "glow_accent": "rgba(255, 51, 85, 0.4)",
        "border_color": "rgba(255, 51, 85, 0.25)",
    },
    "blue": {
        "color_accent": "#2980ff",
        "color_accent_hover": "#1a5ec4",
        "glow_accent": "rgba(41, 128, 255, 0.4)",
        "border_color": "rgba(41, 128, 255, 0.25)",
    },
    "orange": {
        "color_accent": "#ff7700",
        "color_accent_hover": "#cc5500",
        "glow_accent": "rgba(255, 119, 0, 0.4)",
        "border_color": "rgba(255, 119, 0, 0.25)",
    },
}

BACKGROUND_PRESETS: Dict[str, Dict[str, str]] = {
    "black": {
        "bg_primary": "#000000",
        "bg_secondary": "#0a0a0a",
        "bg_card": "rgba(18, 18, 18, 0.85)",
    },
    "oled": {
        "bg_primary": "#000000",
        "bg_secondary": "#050505",
        "bg_card": "rgba(12, 12, 12, 0.90)",
    },
    "midnight": {
        "bg_primary": "#020713",
        "bg_secondary": "#060d20",
        "bg_card": "rgba(8, 16, 36, 0.80)",
    },
    "navy": {
        "bg_primary": "#051329",
        "bg_secondary": "#0c2040",
        "bg_card": "rgba(12, 32, 64, 0.75)",
    },
    "cyberpunk": {
        "bg_primary": "#0d0221",
        "bg_secondary": "#150534",
        "bg_card": "rgba(26, 8, 64, 0.80)",
    },
}


class ThemeManager:
    """Manages dashboard color themes and parses natural-language theme requests."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        if config_path:
            self.config_path = config_path
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.config_path = os.path.join(base_dir, "data", "theme_config.json")

        self.current_theme: Dict[str, str] = dict(DEFAULT_THEME)
        self.load_theme()

    def load_theme(self) -> Dict[str, str]:
        """Load theme configuration from disk."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    if isinstance(saved, dict):
                        self.current_theme.update(saved)
            except Exception as e:
                logger.error("Failed to load theme config: %s", e)
        return self.current_theme

    def save_theme(self) -> bool:
        """Save active theme configuration to disk."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.current_theme, f, indent=2)
            return True
        except Exception as e:
            logger.error("Failed to save theme config: %s", e)
            return False

    def get_theme(self) -> Dict[str, str]:
        """Return the current active theme."""
        return dict(self.current_theme)

    def set_theme_vars(self, updates: Dict[str, str]) -> Dict[str, Any]:
        """Directly update specific theme CSS variables and persist."""
        self.current_theme.update(updates)
        self.save_theme()
        return {
            "status": "ok",
            "theme": self.current_theme,
            "message": "Theme variables successfully updated.",
        }

    def reset_theme(self) -> Dict[str, Any]:
        """Reset theme to default JARVIS futuristic cyan theme."""
        self.current_theme = dict(DEFAULT_THEME)
        self.save_theme()
        return {
            "status": "ok",
            "theme": self.current_theme,
            "message": "Theme reset to default JARVIS cyan.",
        }

    def process_natural_language(self, command: str) -> Dict[str, Any]:
        """Parse natural language theme instructions and apply corresponding styling."""
        text = command.lower().strip()

        # Check reset
        if "reset theme" in text or "default theme" in text:
            return self.reset_theme()

        applied_changes = []

        # Check background presets
        for bg_name, bg_vars in BACKGROUND_PRESETS.items():
            if f"background to {bg_name}" in text or f"{bg_name} background" in text or f"{bg_name} theme" in text:
                self.current_theme.update(bg_vars)
                applied_changes.append(f"background set to {bg_name}")
                break

        # Check accent color presets
        for color_name, color_vars in COLOR_PRESETS.items():
            if f"accent {color_name}" in text or f"accent to {color_name}" in text or f"make accent {color_name}" in text or f"theme {color_name}" in text:
                self.current_theme.update(color_vars)
                applied_changes.append(f"accent color set to {color_name}")
                break

        if applied_changes:
            self.save_theme()
            return {
                "status": "ok",
                "applied": applied_changes,
                "theme": self.current_theme,
                "message": f"Updated theme: {', '.join(applied_changes)}.",
            }

        return {
            "status": "unrecognized",
            "message": "Could not identify specific theme colors. You can say 'Change background to black' or 'Make accent green'.",
        }


theme_manager = ThemeManager()
