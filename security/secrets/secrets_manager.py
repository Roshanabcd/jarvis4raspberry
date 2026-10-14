"""
JARVIS OS - Secrets Manager
Safely loads and manages environment variables and secrets from .env file using python-dotenv.
Never logs secret values. Provides key existence checks and key name enumeration.
"""

import logging
import os
from typing import Dict, List, Optional, Set

try:
    from dotenv import dotenv_values, load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

logger = logging.getLogger("JARVIS.Security.SecretsManager")


class SecretsManager:
    """
    Manages application secrets loaded from .env and system environment variables.
    Guarantees that sensitive secret values are never written to logs or exposed via listings.
    """

    def __init__(self, env_path: Optional[str] = None) -> None:
        self.env_path: Optional[str] = self._resolve_env_path(env_path)
        self._env_keys: Set[str] = set()
        self._load_secrets()

    def _resolve_env_path(self, explicit_path: Optional[str]) -> Optional[str]:
        """Resolves the path to the .env file dynamically without hardcoding."""
        if explicit_path and os.path.exists(explicit_path):
            return os.path.abspath(explicit_path)

        env_from_os = os.environ.get("JARVIS_ENV_FILE")
        if env_from_os and os.path.exists(env_from_os):
            return os.path.abspath(env_from_os)

        # Check in current working directory
        cwd_env = os.path.join(os.getcwd(), ".env")
        if os.path.exists(cwd_env):
            return cwd_env

        # Check in project root relative to this module
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        root_env = os.path.join(project_root, ".env")
        if os.path.exists(root_env):
            return root_env

        # Return root_env even if not yet created (useful for initialization)
        return root_env

    def _load_secrets(self) -> None:
        """Loads secrets from the resolved .env file into environment and internal registry."""
        if not self.env_path or not os.path.exists(self.env_path):
            logger.debug("No .env file found at resolved path: %s", self.env_path)
            return

        try:
            if HAS_DOTENV:
                # Load into os.environ without overwriting pre-existing environment variables
                load_dotenv(dotenv_path=self.env_path, override=False)
                # Read keys configured directly in .env
                file_values: Dict[str, Optional[str]] = dotenv_values(self.env_path)
                self._env_keys.update(file_values.keys())
            else:
                # Fallback parser if python-dotenv is not installed
                logger.warning("python-dotenv not installed. Falling back to internal .env parser.")
                with open(self.env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, val = line.split("=", 1)
                            key = key.strip()
                            val = val.strip().strip("'\"")
                            self._env_keys.add(key)
                            if key not in os.environ:
                                os.environ[key] = val

            logger.info("Successfully loaded secrets configuration from %s (%d keys found)", self.env_path, len(self._env_keys))
        except Exception as exc:
            logger.error("Failed to load secrets from %s: %s", self.env_path, exc)

    def reload(self) -> None:
        """Reloads secrets from the .env file."""
        self._load_secrets()

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieves the secret value for the given key.
        Never logs the secret value.
        """
        val = os.environ.get(key)
        if val is None:
            val = default

        # Log key access safely without ever logging the secret value
        logger.debug("Secret accessed for key: %s (found=%s)", key, val is not None)
        return val

    def has(self, key: str) -> bool:
        """Checks if a secret key exists and has a non-empty value."""
        val = os.environ.get(key)
        return bool(val and len(val.strip()) > 0)

    def list_keys(self) -> List[str]:
        """
        Returns a sorted list of all configured secret key names.
        Values are never included.
        """
        # Return all discovered keys from .env plus any known JARVIS_* keys in os.environ
        keys = set(self._env_keys)
        for k in os.environ.keys():
            if k.startswith("JARVIS_") or k.endswith("_API_KEY") or k.endswith("_SECRET") or k.endswith("_TOKEN"):
                keys.add(k)
        return sorted(list(keys))


# Global singleton instance
secrets_manager = SecretsManager()
