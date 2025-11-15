"""
Configuration loader for the application.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any

# Default configuration
DEFAULT_CONFIG = {
    "vlan_manager": {
        "url": "http://0.0.0.0:9000",
        "sync_interval_seconds": 300
    },
    "application": {
        "host": "0.0.0.0",
        "port": 8000
    },
    "auth": {
        "admin_username": "admin",
        "admin_password": "Password1"
    }
}

# Path to config file
CONFIG_FILE = Path(__file__).parent.parent / "config.json"


class Config:
    """Configuration class for the application."""

    def __init__(self):
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                print(f"✓ Configuration loaded from {CONFIG_FILE}")
                return config
            except Exception as e:
                print(f"⚠ Failed to load config file: {e}, using defaults")
                return DEFAULT_CONFIG
        else:
            print(f"⚠ Config file not found, using defaults")
            return DEFAULT_CONFIG

    @property
    def vlan_manager_url(self) -> str:
        """Get VLAN Manager API URL."""
        return self._config["vlan_manager"]["url"]

    @property
    def sync_interval(self) -> int:
        """Get sync interval in seconds."""
        return self._config["vlan_manager"]["sync_interval_seconds"]

    @property
    def app_host(self) -> str:
        """Get application host."""
        return self._config["application"]["host"]

    @property
    def app_port(self) -> int:
        """Get application port."""
        return self._config["application"]["port"]

    @property
    def admin_username(self) -> str:
        """Get admin username from environment or config."""
        return os.getenv("ADMIN_USERNAME", self._config["auth"]["admin_username"])

    @property
    def admin_password(self) -> str:
        """Get admin password from environment or config."""
        return os.getenv("ADMIN_PASSWORD", self._config["auth"]["admin_password"])

    @property
    def app_title(self) -> str:
        """Get application title from environment or default."""
        return os.getenv("APP_TITLE", "OpenShift Cluster Navigator")


# Global config instance
config = Config()
