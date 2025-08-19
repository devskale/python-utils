"""Pytest configuration and fixtures for strukt2meta tests."""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_markdown_file(temp_dir):
    """Create a sample markdown file for testing."""
    content = """# Test Document

This is a test document for metadata generation.

## Section 1

Some content here.

## Section 2

More content.
"""
    file_path = temp_dir / "test_document.md"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def sample_json_file(temp_dir):
    """Create a sample JSON file for testing."""
    data = {
        "files": [
            {
                "name": "test_document.md",
                "path": "./test_document.md",
                "kategorie": "uncategorized"
            }
        ]
    }
    file_path = temp_dir / "index.json"
    file_path.write_text(json.dumps(data, indent=2))
    return file_path


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    return {
        "name": "Test Document",
        "kategorie": "documentation",
        "begründung": "This is a test document",
        "tags": ["test", "documentation"],
        "summary": "A sample document for testing purposes"
    }


@pytest.fixture
def mock_ai_response():
    """Mock AI API response."""
    return {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "name": "Test Document",
                    "kategorie": "documentation",
                    "begründung": "This is a test document",
                    "tags": ["test", "documentation"]
                })
            }
        }]
    }


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "api_key": "test_key",
        "model": "gpt-3.5-turbo",
        "max_tokens": 1000,
        "temperature": 0.7,
        "index_fields": ["name", "kategorie", "begründung"]
    }


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    with patch('strukt2meta.apicall.OpenAI') as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_file_structure(temp_dir):
    """Create a sample file structure for testing."""
    # Create directories
    (temp_dir / "docs").mkdir()
    (temp_dir / "src").mkdir()
    
    # Create files
    files = {
        "README.md": "# Project README\n\nThis is the main readme.",
        "docs/guide.md": "# User Guide\n\nDetailed user guide.",
        "docs/api.md": "# API Documentation\n\nAPI reference.",
        "src/main.py": "# Main module\nprint('Hello World')",
        "config.json": '{"setting": "value"}'
    }
    
    for file_path, content in files.items():
        full_path = temp_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    
    return temp_dir


@pytest.fixture
def sample_sidecar_file(temp_dir):
    """Create a sample sidecar metadata file."""
    metadata = {
        "name": "Test Document",
        "kategorie": "documentation",
        "begründung": "Generated metadata",
        "generated_at": "2024-01-01T00:00:00Z"
    }
    file_path = temp_dir / "test_document.md.meta.json"
    file_path.write_text(json.dumps(metadata, indent=2))
    return file_path


class MockArgs:
    """Mock command line arguments for testing."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.fixture
def mock_args():
    """Factory for creating mock command line arguments."""
    def _mock_args(**kwargs):
        defaults = {
            'verbose': False,
            'dry_run': False,
            'config': None
        }
        defaults.update(kwargs)
        return MockArgs(**defaults)
    return _mock_args