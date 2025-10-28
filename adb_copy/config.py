"""Configuration management module.

Handles application settings including language preferences.
"""

import json
from pathlib import Path
from typing import Any, Dict


class Config:
    """Application configuration manager.
    
    Stores and retrieves user preferences.
    """
    
    def __init__(self) -> None:
        """Initialize configuration manager."""
        self.config_dir = Path.home() / ".adbcopy"
        self.config_file = self.config_dir / "config.json"
        self._settings: Dict[str, Any] = {}
        self._load()
    
    def _load(self) -> None:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self._settings = json.load(f)
            except Exception:
                self._settings = {}
        else:
            self._settings = {}
    
    def _save(self) -> None:
        """Save configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self._settings[key] = value
        self._save()


# Global configuration instance
_config = Config()


def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value.
    
    Args:
        key: Configuration key
        default: Default value if key not found
        
    Returns:
        Configuration value
    """
    return _config.get(key, default)


def set_config(key: str, value: Any) -> None:
    """Set configuration value.
    
    Args:
        key: Configuration key
        value: Configuration value
    """
    _config.set(key, value)

