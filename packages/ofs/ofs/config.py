"""Configuration management for OFS (Opinionated Filesystem).

Handles loading and managing configuration settings including BASE_DIR.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from .logging import setup_logger

# Import the ConfigProvider protocol
try:
    from .interfaces import ConfigProvider
except ImportError:
    # Fallback for when interfaces module is not available
    from typing import Protocol
    
    class ConfigProvider(Protocol):
        def get_base_dir(self) -> str: ...
        def get_index_file(self) -> str: ...
        def get_metadata_suffix(self) -> str: ...
        def get(self, key: str, default: Any = None) -> Any: ...


class OFSConfig:
    """
    Configuration manager for OFS settings.
    
    Implements the ConfigProvider protocol for dependency injection.
    
    Loads configuration from various sources with the following priority:
    1. Environment variables
    2. Config file in current directory
    3. Config file in user home directory
    4. Default values
    """
    
    DEFAULT_CONFIG = {
        "BASE_DIR": ".dir",
        "INDEX_FILE": ".ofs.index.json",
        "METADATA_SUFFIX": ".meta.json"
    }
    
    def __init__(self):
        """Initialize the configuration manager."""
        self._config = self.DEFAULT_CONFIG.copy()
        self._logger = setup_logger(__name__)
        self._load_config()
    
    def _load_config(self) -> None:
        """
        Load configuration from available sources.
        
        Checks for config files and environment variables to override defaults.
        """
        # Try to load from config file in current directory
        local_config_path = Path("ofs.config.json")
        if local_config_path.exists():
            self._load_config_file(local_config_path)
        
        # Try to load from config file in home directory
        home_config_path = Path.home() / ".ofs" / "config.json"
        if home_config_path.exists():
            self._load_config_file(home_config_path)
        
        # Override with environment variables
        self._load_env_vars()
    
    def _load_config_file(self, config_path: Path) -> None:
        """
        Load configuration from a JSON file.
        
        Args:
            config_path (Path): Path to the configuration file
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                self._config.update(file_config)
        except (json.JSONDecodeError, IOError, PermissionError) as e:
            self._logger.warning(f"Could not load config from {config_path}: {e}")
            # Silently ignore config file errors and use defaults
            pass
    
    def _load_env_vars(self) -> None:
        """
        Load configuration from environment variables.
        
        Environment variables should be prefixed with OFS_
        """
        for key in self.DEFAULT_CONFIG.keys():
            env_key = f"OFS_{key}"
            env_value = os.getenv(env_key)
            if env_value is not None:
                self._config[key] = env_value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key (str): Configuration key
            default (Any): Default value if key not found
            
        Returns:
            Any: Configuration value
        """
        return self._config.get(key, default)
    
    def get_base_dir(self) -> str:
        """
        Get the BASE_DIR configuration value.
        
        Returns:
            str: The base directory path
        """
        return self._config["BASE_DIR"]
    
    def get_index_file(self) -> str:
        """
        Get the INDEX_FILE configuration value.
        
        Returns:
            str: The index file name
        """
        return self._config["INDEX_FILE"]
    
    def get_metadata_suffix(self) -> str:
        """
        Get the METADATA_SUFFIX configuration value.
        
        Returns:
            str: The metadata file suffix
        """
        return self._config["METADATA_SUFFIX"]
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key (str): Configuration key
            value (Any): Configuration value
        """
        self._config[key] = value
    
    def save_config(self, config_path: Optional[Path] = None) -> None:
        """
        Save current configuration to a file.
        
        Args:
            config_path (Optional[Path]): Path to save config file.
                                        Defaults to ofs.config.json in current directory.
        """
        if config_path is None:
            config_path = Path("ofs.config.json")
        
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
        except (IOError, OSError, PermissionError) as e:
            self._logger.error(f"Error saving config to {config_path}: {e}")
            raise RuntimeError(f"Failed to save config file: {e}")


# Global configuration instance
_config_instance = None


def get_config() -> OFSConfig:
    """
    Get the global configuration instance.
    
    Returns:
        OFSConfig: The global configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = OFSConfig()
    return _config_instance


def get_base_dir() -> str:
    """
    Get the BASE_DIR from configuration.
    
    Returns:
        str: The base directory path
    """
    return get_config().get_base_dir()