"""
Configuration manager for desktop app
"""
import json
from pathlib import Path
from typing import Any, Dict


class ConfigManager:
    """Manages application configuration"""

    def __init__(self, config_path: str = None):
        """
        Initialize configuration manager

        Args:
            config_path: Path to config file (defaults to app/resources/config/settings.json)
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "resources" / "config" / "settings.json"

        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load configuration from file"""
        if not self.config_path.exists():
            # Create default config
            default_config = self._get_default_config()
            self.save_config(default_config)
            return default_config

        with open(self.config_path, 'r') as f:
            return json.load(f)

    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "app": {
                "name": "SLR Citation Processor",
                "version": "1.0.0"
            },
            "google": {
                "spreadsheet_id": "",
                "drive_folder_id": ""
            },
            "llm": {
                "provider": "openai",  # or "anthropic"
                "model": "gpt-4o-mini",
                "api_key": ""
            },
            "paths": {
                "credentials": "app/resources/credentials.enc",
                "cache_dir": "cache",
                "output_dir": "output"
            },
            "processing": {
                "max_concurrent_downloads": 5,
                "retry_attempts": 3,
                "timeout_seconds": 30
            },
            "ui": {
                "theme": "light",
                "window_size": [1200, 800]
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key

        Args:
            key: Configuration key (e.g., "google.spreadsheet_id")
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """
        Set configuration value by dot-notation key

        Args:
            key: Configuration key (e.g., "google.spreadsheet_id")
            value: Value to set
        """
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save_config(self, config: Dict = None):
        """
        Save configuration to file

        Args:
            config: Configuration dict (uses self.config if not provided)
        """
        if config is None:
            config = self.config

        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)

    def update(self, updates: Dict):
        """
        Update multiple configuration values

        Args:
            updates: Dict of updates to apply
        """
        def deep_update(base: dict, updates: dict):
            for key, value in updates.items():
                if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                    deep_update(base[key], value)
                else:
                    base[key] = value

        deep_update(self.config, updates)

    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config = self._get_default_config()
        self.save_config()
