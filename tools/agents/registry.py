"""
AI Agent Registry for JARVIS OS.
Dynamically discovers installed AI coding agent CLIs, inspects non-secret authentication
status, capabilities, and maintains the authoritative agent inventory.
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.agents.adapters.antigravity_adapter import AntigravityAdapter
from tools.agents.adapters.base import BaseAgentAdapter
from tools.agents.adapters.claude_adapter import ClaudeAdapter
from tools.agents.adapters.codex_adapter import CodexAdapter
from tools.agents.adapters.ollama_adapter import OllamaAdapter
from tools.agents.adapters.opencode_adapter import OpenCodeAdapter
from tools.agents.models import AgentCapabilities, AgentId, AgentMetadata, AgentStatus

logger = logging.getLogger("JARVIS.AgentRegistry")


class AgentRegistry:
    """Discovers, validates, and registers AI coding agents on the Raspberry Pi."""

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = Path(storage_dir or "/home/roshan/.gemini/antigravity/scratch/jarvis-os/data/agents")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.storage_dir / "registry.json"

        self._adapters: Dict[str, BaseAgentAdapter] = {
            AgentId.ANTIGRAVITY.value: AntigravityAdapter(),
            AgentId.CODEX.value: CodexAdapter(),
            AgentId.CLAUDE.value: ClaudeAdapter(),
            AgentId.OPENCODE.value: OpenCodeAdapter(),
            AgentId.OLLAMA.value: OllamaAdapter(),
        }
        self._metadata_cache: Dict[str, AgentMetadata] = {}
        self._load_from_disk()

    def get_adapter(self, agent_id: str) -> Optional[BaseAgentAdapter]:
        """Retrieve the adapter for a given agent identifier."""
        return self._adapters.get(agent_id.lower().strip())

    def discover_all(self, force_refresh: bool = False) -> List[AgentMetadata]:
        """Discover all installed agents and their live capability states."""
        if not force_refresh and self._metadata_cache:
            return list(self._metadata_cache.values())

        results: List[AgentMetadata] = []
        for agent_id, adapter in self._adapters.items():
            try:
                meta = adapter.discover()
                self._metadata_cache[agent_id] = meta
                results.append(meta)
            except Exception as e:
                logger.error("Error discovering agent '%s': %s", agent_id, e)
                err_meta = AgentMetadata(
                    id=agent_id,
                    display_name=adapter.display_name,
                    installed=False,
                    authenticated=False,
                    status=AgentStatus.ERROR,
                    error_message=str(e),
                )
                self._metadata_cache[agent_id] = err_meta
                results.append(err_meta)

        self._save_to_disk()
        return results

    def _load_from_disk(self) -> None:
        """Load cached metadata from disk on startup."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for k, d in data.items():
                    raw_caps = d.get("capabilities", {})
                    caps = AgentCapabilities(**raw_caps)
                    meta = AgentMetadata(
                        id=d["id"],
                        display_name=d["display_name"],
                        installed=d.get("installed", False),
                        authenticated=d.get("authenticated", False),
                        version=d.get("version"),
                        cli_path=d.get("cli_path"),
                        capabilities=caps,
                        permission_mode=d.get("permission_mode", "prompt"),
                        last_health_check=d.get("last_health_check", time.time()),
                        status=AgentStatus(d.get("status", "NOT_INSTALLED")),
                        error_message=d.get("error_message"),
                    )
                    self._metadata_cache[k] = meta
            except Exception as e:
                logger.warning("Could not load agent registry from disk: %s", e)

    def get_metadata(self, agent_id: str) -> Optional[AgentMetadata]:
        """Get metadata for a specific agent (discovering if not cached)."""
        aid = agent_id.lower().strip()
        if aid not in self._metadata_cache:
            adapter = self._adapters.get(aid)
            if adapter:
                self._metadata_cache[aid] = adapter.discover()
        return self._metadata_cache.get(aid)

    def get_ready_agents(self) -> List[AgentMetadata]:
        """Return only agents that are installed and authenticated."""
        all_meta = self.discover_all()
        return [m for m in all_meta if m.status == AgentStatus.READY]

    def _save_to_disk(self) -> None:
        """Persist discovery state safely to disk without secrets."""
        try:
            data = {k: v.to_dict() for k, v in self._metadata_cache.items()}
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning("Failed to save registry to disk: %s", e)


agent_registry = AgentRegistry()
