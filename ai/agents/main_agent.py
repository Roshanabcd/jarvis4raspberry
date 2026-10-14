"""Main orchestrator agent for JARVIS OS."""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from ai.agents.base_agent import BaseAgent
from ai.agents.file_agent import FileAgent
from ai.agents.robotics_agent import RoboticsAgent
from ai.agents.sensor_agent import SensorAgent
from ai.agents.system_agent import SystemAgent
from ai.agents.vision_agent import VisionAgent
from ai.prompts.system_prompt import JARVIS_SYSTEM_PROMPT
from ai.router.model_router import ModelRouter

logger = logging.getLogger("JARVIS.MainAgent")


class MainAgent(BaseAgent):
    """Central orchestrator that routes queries to specialized sub-agents."""

    _shared_instance: Optional["MainAgent"] = None

    def __init__(
        self,
        router: Optional[ModelRouter] = None,
        robotics_agent: Optional[BaseAgent] = None,
        sensor_agent: Optional[BaseAgent] = None,
        vision_agent: Optional[BaseAgent] = None,
        file_agent: Optional[BaseAgent] = None,
        system_agent: Optional[BaseAgent] = None,
    ):
        super().__init__(
            name="MainAgent",
            description="Coordinates intent classification, sub-agent delegation, and general AI responses.",
        )
        self.router = router or ModelRouter()
        self.robotics_agent = robotics_agent or RoboticsAgent()
        self.sensor_agent   = sensor_agent   or SensorAgent()
        self.vision_agent   = vision_agent   or VisionAgent()
        self.file_agent     = file_agent     or FileAgent()
        self.system_agent   = system_agent   or SystemAgent()

        self.delegation_rules: List[Tuple[List[str], BaseAgent, str]] = [
            (["robot", "motor", "servo", "forward", "backward", "rotate", "estop"], self.robotics_agent, "robotics"),
            (["temp", "temperature", "sensor", "bme", "humidity", "light", "lux", "distance", "obstacle", "motion", "pir"], self.sensor_agent, "sensor"),
            (["camera", "vision", "see", "capture", "photo", "image", "describe", "detect"], self.vision_agent, "vision"),
            (["file", "read file", "write file", "create file", "list files", "search files"], self.file_agent, "file"),
            (["system", "cpu", "ram", "disk", "memory usage", "temperature", "uptime", "status", "process"], self.system_agent, "system"),
        ]

    @classmethod
    def get_instance(cls) -> "MainAgent":
        if cls._shared_instance is None:
            cls._shared_instance = cls()
        return cls._shared_instance

    def _matches_keywords(self, text: str, keywords: List[str]) -> bool:
        for kw in keywords:
            pattern = rf"\b{re.escape(kw)}\b"
            if re.search(pattern, text):
                return True
        return False

    def handle(self, query: str, context: Optional[Any] = None) -> str:
        q_lower = query.lower()
        logger.info("MainAgent evaluating: '%s'", query[:80])

        for keywords, agent, domain in self.delegation_rules:
            if self._matches_keywords(q_lower, keywords):
                logger.info("→ Delegating to %s agent", domain)
                return agent.handle(query, context)

        logger.info("→ Routing to AI model router")
        merged: Dict[str, Any] = {"system_prompt": JARVIS_SYSTEM_PROMPT}
        if isinstance(context, dict):
            merged.update(context)
        elif isinstance(context, list):
            merged["history"] = context

        return self.router.route(query, task_type="general", context=merged)
