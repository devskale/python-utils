"""Pytest configuration and fixtures for strukt2meta tests."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock

from tests.fixtures.test_utils import MockArgs


@pytest.fixture
def mock_args():
    """Provide a mock args object for testing commands."""
    return MockArgs(
        source_file=None,
        target_file=None,
        prompt="metadata_extraction",
        output_file=None,
        dry_run=False,
        verbose=False,
        overwrite=False,
        model="gpt-4",
        temperature=0.7,
        max_tokens=1000,
        directory=None,
        json_file=None,
        fields=None,
        num=5,
        mode="standard",
        step=None
    )


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_markdown_content():
    """Provide sample markdown content for testing."""
    return """# Test Document

This is a test document with some content.

## Section 1

Some content here.

## Section 2

More content here.
"""


@pytest.fixture
def sample_metadata():
    """Provide sample metadata for testing."""
    return {
        "title": "Test Document",
        "description": "A test document for unit testing",
        "category": "test",
        "tags": ["test", "document"],
        "author": "Test Author",
        "created_date": "2024-01-01"
    }


@pytest.fixture
def sample_json_data():
    """Provide sample JSON data structure for testing."""
    return {
        "files": [
            {
                "name": "test1.md",
                "path": "/path/to/test1.md",
                "metadata": {
                    "title": "Test 1",
                    "category": "test"
                }
            },
            {
                "name": "test2.md",
                "path": "/path/to/test2.md",
                "metadata": {
                    "title": "Test 2",
                    "category": "test"
                }
            }
        ],
        "un_items": [
            {
                "name": "uncategorized.pdf",
                "path": "/path/to/uncategorized.pdf"
            }
        ]
    }


@pytest.fixture
def mock_ai_model():
    """Provide a mock AI model for testing."""
    mock = Mock()
    mock.query.return_value = '{"title": "Generated Title", "description": "Generated description"}'
    return mock