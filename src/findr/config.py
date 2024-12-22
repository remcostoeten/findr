"""
Configuration management for the Findr tool.
"""
from typing import Dict, Any
import json
from pathlib import Path
import os

DEFAULT_CONFIG = {
    # Search settings
    "fuzzy_threshold": 80,  # Minimum score for fuzzy matching (0-100)
    "max_results": 100,     # Maximum number of results to display
    "max_depth": None,      # Maximum directory depth (None for unlimited)
    "follow_symlinks": False,
    "search_hidden": False,
    "binary_size_limit": 1024 * 1024,  # Skip files larger than 1MB for content search
    "cache_size_limit": 1024 * 100,    # Cache files smaller than 100KB
    
    # Search presets
    "presets": {
        "google_keys": {
            "name": "Google API Keys",
            "description": "Find Google-related keys in env files",
            "extensions": [".env", ".env.local", ".env.development", ".env.production"],
            "exclude_dirs": ["node_modules", ".git", "dist", ".build"],
            "max_size": "1M",
            "content_patterns": ["GOOGLE_"],
            "ignore_case": False
        },
        "secrets": {
            "name": "Find Secret Files",
            "description": "Search for configuration and secret files",
            "extensions": [".env", ".env.local", ".env.development", ".env.production", ".pem", ".key"],
            "exclude_dirs": [".build", "dist", "node_modules"],
            "max_size": "2M",
            "content_patterns": ["API_KEY", "SECRET", "PASSWORD", "TOKEN", "PRIVATE_KEY"],
            "ignore_case": True
        },
        "configs": {
            "name": "Configuration Files",
            "description": "Search for various config files",
            "extensions": [".json", ".yaml", ".yml", ".toml", ".ini", ".conf"],
            "exclude_dirs": ["node_modules", "venv", ".git"],
            "max_size": "1M"
        },
        "media": {
            "name": "Media Files",
            "description": "Search for media files",
            "extensions": [".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mp3", ".wav"],
            "min_size": "10K",
            "max_size": "100M"
        },
        "code": {
            "name": "Source Code",
            "description": "Search in source code files",
            "extensions": [".py", ".js", ".ts", ".jsx", ".tsx", ".cpp", ".java"],
            "exclude_dirs": ["node_modules", "venv", "dist", ".build"],
            "max_size": "1M"
        }
    },
    
    # File patterns
    "default_excludes": [
        "node_modules",
        ".git",
        "__pycache__",
        ".next",
        "dist",
        ".build",
        "venv",
        "env"
    ],
    "default_extensions": [
        "*.{js,jsx,ts,tsx}",  # Web development
        "*.{py,pyc}",         # Python
        "*.{java,class}",     # Java
        "*.{c,cpp,h,hpp}",    # C/C++
        "*.{rs,go,rb}",       # Rust/Go/Ruby
        "*.{html,css,scss}"   # Web markup/styling
    ],
    
    # Display settings
    "date_format": "%Y-%m-%d %H:%M",
    "sort_by": "path",        # path, size, modified, matches
    "sort_reverse": False,
    "show_preview": True,
    "preview_length": 200,    # Characters to show in preview
    "theme": {
        "path": "blue",
        "size": "green",
        "date": "yellow",
        "match": "red bold",
        "preview": "dim",
        "error": "red bold",
        "warning": "yellow",
        "info": "blue"
    },
    
    # Performance settings
    "use_cache": True,
    "parallel_search": True,
    "max_workers": None,      # None = use CPU count
    
    # Content search settings
    "context_lines": 2,       # Lines of context around matches
    "ignore_case": True,
    "whole_word": False,
    "regex_search": False,
    
    # History settings
    "save_history": True,
    "history_file": "~/.findr_history",
    "max_history": 1000
}

class Config:
    def __init__(self):
        self._config = DEFAULT_CONFIG.copy()
        self.load_user_config()
        
    def load_user_config(self):
        """Load user configuration from ~/.findr/config.json"""
        config_dir = Path.home() / ".findr"
        config_file = config_dir / "config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                self._config.update(user_config)
            except json.JSONDecodeError:
                print("Warning: Invalid user config file")
                
    def save_user_config(self):
        """Save current configuration to user config file"""
        config_dir = Path.home() / ".findr"
        config_file = config_dir / "config.json"
        
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(self._config, f, indent=4)
        except OSError as e:
            print(f"Error saving config: {e}")
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)
        
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self._config[key] = value
        
    def update(self, updates: Dict[str, Any]):
        """Update multiple configuration values"""
        self._config.update(updates)
        
    def reset(self):
        """Reset configuration to defaults"""
        self._config = DEFAULT_CONFIG.copy()

    @property
    def config(self) -> dict:
        """Get the entire configuration dictionary"""
        return self._config

