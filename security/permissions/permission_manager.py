"""Permission Manager for JARVIS OS.

Enforces multi-tiered access control (Risk Levels 0-4) based on policies
defined in config/permissions.yaml. High-risk actions require explicit user confirmation.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional
import yaml

from config.config_manager import config

logger = logging.getLogger("JARVIS-PERMISSIONS")


class PermissionManager:
    """Manages tool execution permissions and security risk gates."""

    # Risk level constants
    RISK_NONE = 0
    RISK_LOW = 1
    RISK_MODERATE = 2
    RISK_HIGH = 3
    RISK_CRITICAL = 4

    def __init__(self, config_file: Optional[str] = None) -> None:
        """Initialize PermissionManager and load policies from configuration.

        Args:
            config_file: Optional path to permissions.yaml file.
        """
        self.config_file = config_file or self._find_config_file()
        self.default_max_risk: int = 2
        self.require_confirmation_above: int = 3
        self.allowed_tools: List[str] = []
        self.denied_tools: List[str] = []
        self.high_risk_tools: List[str] = []
        self.reload_permissions()

    def _find_config_file(self) -> str:
        """Locate permissions.yaml path dynamically without hardcoding."""
        # 1. Check ConfigManager if available
        if hasattr(config, "config_dir") and config.config_dir:
            candidate = os.path.join(config.config_dir, "permissions.yaml")
            if os.path.exists(candidate):
                return candidate

        # 2. Check relative to this module
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(module_dir))
        candidate = os.path.join(project_root, "config", "permissions.yaml")
        if os.path.exists(candidate):
            return candidate

        # Fallback to current working directory config
        return os.path.abspath("config/permissions.yaml")

    def reload_permissions(self) -> None:
        """Reload configuration policies from permissions.yaml."""
        if not os.path.exists(self.config_file):
            logger.warning(f"Permissions config not found at {self.config_file}. Using safe defaults.")
            self.default_max_risk = 2
            self.require_confirmation_above = 3
            self.allowed_tools = [
                "system_status",
                "read_file",
                "write_file",
                "run_command",
                "sensor_read",
                "memory_search",
            ]
            self.denied_tools = []
            self.high_risk_tools = ["delete_file", "motor_control", "push_git", "install_package"]
            return

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = yaml.safe_load(f) or {}

            self.default_max_risk = int(data.get("default_max_risk", 2))
            self.require_confirmation_above = int(data.get("require_confirmation_above", 3))
            self.allowed_tools = list(data.get("allowed_tools", []))
            self.denied_tools = list(data.get("denied_tools", []))
            self.high_risk_tools = list(data.get("high_risk_tools", []))

            logger.info(
                f"Loaded permissions: max_risk={self.default_max_risk}, "
                f"confirm_above={self.require_confirmation_above}, "
                f"allowed={len(self.allowed_tools)}, denied={len(self.denied_tools)}, "
                f"high_risk={len(self.high_risk_tools)}"
            )
        except Exception as exc:
            logger.error(f"Error loading permissions config: {exc}", exc_info=True)

    def check_permission(self, tool_name: str, risk_level: int = 0, confirmed: bool = False) -> bool:
        """Evaluate if an action is permitted based on risk, policies, and confirmation.

        Args:
            tool_name: The identifier of the tool being executed.
            risk_level: The declared risk level of the operation (0-4).
            confirmed: Whether the user has provided explicit confirmation.

        Returns:
            bool: True if execution is permitted, False otherwise.
        """
        # 1. Deny list has absolute precedence
        if tool_name in self.denied_tools:
            logger.warning(f"Tool '{tool_name}' explicitly denied by policy.")
            return False

        # 2. Effective risk calculation
        is_marked_high_risk = tool_name in self.high_risk_tools
        effective_risk = max(risk_level, 3) if is_marked_high_risk else risk_level

        # 3. High risk (3-4) or above confirmation threshold requires explicit confirmation
        if effective_risk >= self.require_confirmation_above or effective_risk >= self.RISK_HIGH:
            if not confirmed:
                logger.warning(
                    f"Tool '{tool_name}' (effective risk={effective_risk}) denied without confirmation."
                )
                return False
            return True

        # 4. If not confirmed, risk must not exceed default_max_risk
        if effective_risk > self.default_max_risk and not confirmed:
            logger.warning(
                f"Tool '{tool_name}' risk {effective_risk} exceeds default maximum {self.default_max_risk}."
            )
            return False

        return True

    def is_high_risk(self, tool_name: str, risk_level: int = 0) -> bool:
        """Check if a tool or operation is considered high risk."""
        return tool_name in self.high_risk_tools or risk_level >= self.RISK_HIGH


# Global permission manager instance
permission_manager = PermissionManager()
