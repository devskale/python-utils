"""
Tests for the core OFS functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from ofs.core import (
    get_path, 
    get_ofs_root, 
    list_ofs_items,
    find_bidder_in_project,
    list_projects,
    list_bidders
)
from ofs.config import get_config


def test_get_path():
    """Test the get_path function."""
    path = get_path("test_doc")
    assert isinstance(path, str)
    assert path.endswith("test_doc")
    assert ".dir" in path


def test_get_path_with_existing_project():
    """Test get_path with an existing project name."""
    # This should find the actual project if it exists
    path = get_path("Demoprojekt1")
    assert isinstance(path, str)
    assert "Demoprojekt1" in path


def test_get_ofs_root():
    """Test the get_ofs_root function."""
    root = get_ofs_root()
    assert isinstance(root, str)
    assert len(root) > 0


def test_list_ofs_items():
    """Test the list_ofs_items function."""
    items = list_ofs_items()
    assert isinstance(items, list)
    # Items should be strings
    for item in items:
        assert isinstance(item, str)


def test_list_projects():
    """Test the list_projects function."""
    projects = list_projects()
    assert isinstance(projects, list)
    # Projects should be strings
    for project in projects:
        assert isinstance(project, str)


def test_list_bidders():
    """Test the list_bidders function."""
    # Test with a known project
    bidders = list_bidders("Demoprojekt1")
    assert isinstance(bidders, list)
    # Bidders should be strings
    for bidder in bidders:
        assert isinstance(bidder, str)
    
    # Test with non-existent project
    empty_bidders = list_bidders("NonExistentProject")
    assert isinstance(empty_bidders, list)
    assert len(empty_bidders) == 0


def test_find_bidder_in_project():
    """Test the find_bidder_in_project function."""
    # Test with existing project and bidder
    bidders = list_bidders("Demoprojekt1")
    if bidders:
        # Use the first available bidder
        first_bidder = bidders[0]
        path = find_bidder_in_project("Demoprojekt1", first_bidder)
        if path:  # Only test if bidder is actually found
            assert isinstance(path, str)
            assert "Demoprojekt1" in path
            assert first_bidder in path
    
    # Test with non-existent combination
    path = find_bidder_in_project("NonExistentProject", "NonExistentBidder")
    assert path is None


def test_config_integration():
    """Test that configuration is properly integrated."""
    config = get_config()
    base_dir = config.get("BASE_DIR", ".dir")
    
    # Test that get_path uses the configured BASE_DIR
    path = get_path("test_integration")
    assert base_dir in path
    assert path.endswith("test_integration")