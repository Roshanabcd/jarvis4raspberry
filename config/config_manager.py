import os
import yaml
import logging
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_dir: str = None):
        if not config_dir or not os.path.exists(config_dir):
            self.config_dir = os.path.dirname(os.path.abspath(__file__))
        else:
            self.config_dir = config_dir
        self.config: Dict[str, Any] = {}
        self.load_all()

    def load_all(self):
        files = ['config.yaml', 'hardware.yaml', 'models.yaml', 'permissions.yaml']
        for file in files:
            path = os.path.join(self.config_dir, file)
            if not os.path.exists(path):
                fallback_path = os.path.join(os.path.dirname(__file__), file)
                if os.path.exists(fallback_path):
                    path = fallback_path
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = yaml.safe_load(f)
                    if data:
                        self.config.update(data)
            else:
                logging.warning(f"Config file {file} not found.")
                
    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.config[key] = value

    def save(self, filename: str = "config.yaml") -> bool:
        """Atomically persist active configuration to disk."""
        path = os.path.join(self.config_dir, filename)
        temp_path = f"{path}.tmp"
        try:
            with open(temp_path, "w") as f:
                yaml.safe_dump(self.config, f, default_flow_style=False, sort_keys=False)
            os.replace(temp_path, path)
            logging.info(f"Configuration successfully persisted to {path}")
            return True
        except Exception as e:
            logging.error(f"Failed to save configuration to {path}: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False

    def save_env(self, updates: Dict[str, str]) -> bool:
        """Update or insert key-values into .env file safely."""
        env_path = os.path.join(os.path.dirname(self.config_dir), ".env")
        if not os.path.exists(env_path):
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                lines = f.readlines()

        temp_env = f"{env_path}.tmp"
        try:
            import tempfile
            from dotenv import set_key
            # Keep existing settings and quote values with python-dotenv's parser.
            # A private, unique temporary file avoids exposing newly entered keys.
            fd, temp_env = tempfile.mkstemp(prefix=".env-", dir=os.path.dirname(env_path))
            with os.fdopen(fd, "w") as f:
                f.writelines(lines)
            for key, value in updates.items():
                if not key.replace("_", "").isalnum() or any(c in value for c in ('\n', '\r', '\x00')):
                    raise ValueError("Invalid environment setting")
                set_key(temp_env, key, value, quote_mode="always")
            with open(temp_env, "rb") as f:
                os.fsync(f.fileno())
            os.replace(temp_env, env_path)
            logging.info(f"Environment variables successfully persisted to {env_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to save .env: {e}")
            if os.path.exists(temp_env):
                os.remove(temp_env)
            return False

_default_config_dir = os.path.dirname(__file__)
if not os.path.exists(os.path.join(_default_config_dir, 'config.yaml')):
    _alt_dir = os.path.join(_default_config_dir, '../../config')
    if os.path.exists(_alt_dir):
        _default_config_dir = _alt_dir

config = ConfigManager(_default_config_dir)
