"""
Configuration management functionality.
"""
import json
from pathlib import Path
from typing import Dict, List

class Config:
    def __init__(self):
        self.config_file = Path.home() / '.search_tool_config.json'
        self.search_history_file = Path.home() / '.search_tool_history.json'

    def load_config(self) -> dict:
        """Load saved configurations"""
        if self.config_file.exists():
            with open(self.config_file) as f:
                return json.load(f)
        return {}

    def save_config(self, config: dict):
        """Save current configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def save_search_history(self, params: dict):
        """Save search parameters to history"""
        # [Previous implementation]
        pass

    def load_recent_searches(self) -> List[dict]:
        """Load recent search configurations"""
        # [Previous implementation]
        pass

