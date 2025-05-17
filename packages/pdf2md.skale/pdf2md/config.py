# config.py - Configuration management for PDF to Markdown conversion

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ConfigManager:
    """Manage configuration settings for PDF to Markdown conversion."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Load environment variables
        # First try loading from current working directory, then fall back to default behavior
        load_dotenv(dotenv_path=os.path.join(
            os.getcwd(), '.env'), override=True)
        load_dotenv(override=True)

        # Default settings
        self._config = {
            # Default directories
            'root_folder': os.getenv('ROOT_FOLDER', ''),
            'default_input_dir': '',
            'default_output_dir': 'md',

            # OCR settings
            'ocr_language': 'deu',

            # Default parser
            'default_parser': 'pdfplumber',

            # API keys
            'llama_cloud_api_key': os.getenv('LLAMA_CLOUD_API_KEY', ''),

            # Performance settings
            'pytorch_mps_high_watermark_ratio': '0.0',
            'pytorch_enable_mps_fallback': '1',
        }

        # Set environment variables for libraries that need them
        os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = self._config['pytorch_mps_high_watermark_ratio']
        os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = self._config['pytorch_enable_mps_fallback']

        self._initialized = True

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value

        # Update environment variables if needed
        if key == 'pytorch_mps_high_watermark_ratio':
            os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = str(value)
        elif key == 'pytorch_enable_mps_fallback':
            os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = str(value)

    def update(self, config_dict: Dict[str, Any]) -> None:
        """Update multiple configuration values."""
        for key, value in config_dict.items():
            self.set(key, value)

    def get_input_directory(self) -> str:
        """Get the default input directory."""
        return os.path.join(self.get('root_folder'), self.get('default_input_dir'))

    def get_output_directory(self, input_dir: Optional[str] = None) -> str:
        """Get the default output directory based on input directory."""
        if input_dir is None:
            input_dir = self.get_input_directory()
        return os.path.join(input_dir, self.get('default_output_dir'))

    def get_api_key(self, service: str) -> Optional[str]:
        """Get an API key for a specific service."""
        key_map = {
            'llamaparse': 'llama_cloud_api_key',
        }
        config_key = key_map.get(service)
        if config_key:
            return self.get(config_key)
        return None


# Create a singleton instance
config = ConfigManager()
