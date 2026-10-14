"""File management agent stub for safe I/O operations."""

import logging
from typing import Any, Dict, Optional
from ai.agents.base_agent import BaseAgent
from config.config_manager import config

logger = logging.getLogger("JARVIS-FILE-AGENT")


class FileAgent(BaseAgent):
    """Agent stub handling file reading, writing, and storage inspection."""

    def __init__(self):
        super().__init__(
            name="FileAgent",
            description="Performs monitored file reading, writing, and directory inspections.",
        )
        self.simulation_mode = config.get("simulation_mode", True)

    def handle(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process file operations or inspect stored assets."""
        logger.info("FileAgent handling query: '%s'", query)
        q = query.lower()
        if "read" in q:
            return "File subsystem: Safe read completed. Target path accessible."
        elif "write" in q:
            if self.simulation_mode:
                return "File subsystem (simulated): Monitored write operation verified. No changes committed."
            return "File subsystem: File write operation executed successfully."
        else:
            return "File subsystem: Ready for verified file operations."
