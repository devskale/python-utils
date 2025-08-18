"""
Tests for the OFS configuration functionality.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from ofs.config import OFSConfig, get_config, get_base_dir


def test_default_config():
    """
    Test that default configuration values are set correctly.
    """
    config = OFSConfig()
    assert config.get("BASE_DIR") == ".dir"
    assert config.get("INDEX_FILE") == ".ofs.index.json"
    assert config.get("METADATA_SUFFIX") == ".meta.json"


def test_get_base_dir():
    """
    Test the get_base_dir convenience function.
    """
    base_dir = get_base_dir()
    assert base_dir == ".dir"


def test_config_file_loading():
    """
    Test loading configuration from a file.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test config file
        config_file = Path(temp_dir) / "ofs.config.json"
        test_config = {
            "BASE_DIR": "custom_dir",
            "INDEX_FILE": "custom_index.json"
        }

        with open(config_file, 'w') as f:
            json.dump(test_config, f)

        # Change to temp directory and create config
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            config = OFSConfig()
            assert config.get("BASE_DIR") == "custom_dir"
            assert config.get("INDEX_FILE") == "custom_index.json"
            # Default values should still be present for unspecified keys
            assert config.get("METADATA_SUFFIX") == ".meta.json"
        finally:
            os.chdir(original_cwd)


def test_environment_variable_override():
    """
    Test that environment variables override config file values.
    """
    # Set environment variable
    os.environ["OFS_BASE_DIR"] = "env_dir"

    try:
        config = OFSConfig()
        assert config.get("BASE_DIR") == "env_dir"
    finally:
        # Clean up environment variable
        if "OFS_BASE_DIR" in os.environ:
            del os.environ["OFS_BASE_DIR"]


def test_config_set_and_get():
    """
    Test setting and getting configuration values.
    """
    config = OFSConfig()
    config.set("CUSTOM_KEY", "custom_value")
    assert config.get("CUSTOM_KEY") == "custom_value"
    assert config.get("NONEXISTENT_KEY", "default") == "default"


def test_save_config():
    """
    Test saving configuration to a file.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        config = OFSConfig()
        config.set("BASE_DIR", "saved_dir")

        config_file = Path(temp_dir) / "test_config.json"
        config.save_config(config_file)

        # Verify file was created and contains correct data
        assert config_file.exists()
        with open(config_file, 'r') as f:
            saved_data = json.load(f)

        assert saved_data["BASE_DIR"] == "saved_dir"
