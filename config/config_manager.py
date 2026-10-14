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

_default_config_dir = os.path.dirname(__file__)
if not os.path.exists(os.path.join(_default_config_dir, 'config.yaml')):
    _alt_dir = os.path.join(_default_config_dir, '../../config')
    if os.path.exists(_alt_dir):
        _default_config_dir = _alt_dir

config = ConfigManager(_default_config_dir)
