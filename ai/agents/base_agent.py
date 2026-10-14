"""Abstract base agent class for specialized JARVIS OS agents."""

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("JARVIS-AGENT")


class BaseAgent(ABC):
    """Abstract base class for all specialized domain agents in JARVIS OS."""

    def __init__(self, name: str, description: str):
        """Initialize the base agent.

        Args:
            name: Identifier for the agent.
            description: Short summary of the agent's domain and responsibilities.
        """
        self.name = name
        self.description = description

    @abstractmethod
    def handle(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process an incoming query within this agent's domain.

        Args:
            query: The user or system request string.
            context: Optional context dictionary.

        Returns:
            A formatted string response representing the action result or reply.
        """
        pass
