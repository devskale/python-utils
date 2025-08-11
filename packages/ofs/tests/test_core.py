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


def test_list_bidder_docs_json():
    """Test the list_bidder_docs_json function."""
    from ofs.core import list_bidder_docs_json
    
    # Test with existing project and bidder (with metadata - default behavior)
    result_with_meta = list_bidder_docs_json("Demoprojekt1", "Demo2", include_metadata=True)
    assert isinstance(result_with_meta, dict)
    assert 'project' in result_with_meta
    assert 'bidder' in result_with_meta
    assert 'documents' in result_with_meta
    assert 'total_documents' in result_with_meta
    assert result_with_meta['project'] == "Demoprojekt1"
    assert result_with_meta['bidder'] == "Demo2"
    assert isinstance(result_with_meta['documents'], list)
    assert isinstance(result_with_meta['total_documents'], int)
    
    # Test with existing project and bidder (without metadata)
    result_without_meta = list_bidder_docs_json("Demoprojekt1", "Demo2", include_metadata=False)
    assert isinstance(result_without_meta, dict)
    assert 'project' in result_without_meta
    assert 'bidder' in result_without_meta
    assert 'documents' in result_without_meta
    assert 'total_documents' in result_without_meta
    assert result_without_meta['project'] == "Demoprojekt1"
    assert result_without_meta['bidder'] == "Demo2"
    assert isinstance(result_without_meta['documents'], list)
    assert isinstance(result_without_meta['total_documents'], int)
    
    # Both results should have the same number of documents
    assert result_with_meta['total_documents'] == result_without_meta['total_documents']
    
    # Verify that only allowed document types are included in both cases
    for result in [result_with_meta, result_without_meta]:
        for doc in result['documents']:
            filename = doc['name'].lower()
            # Should not contain JSON or markdown files
            assert not filename.endswith('.json')
            assert not filename.endswith('.md')
            assert not filename.endswith('.markdown')
            # Should contain allowed extensions
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', 
                                '.tiff', '.tif', '.svg', '.webp', '.doc', '.docx', 
                                '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', 
                                '.odp', '.rtf', '.txt']
            assert any(filename.endswith(ext) for ext in allowed_extensions)
    
    # Check that metadata is included when requested
    for doc in result_with_meta['documents']:
        if 'metadata' in doc:
            metadata = doc['metadata']
            assert 'size' in metadata
            assert 'parsers' in metadata
            assert 'meta' in metadata
            # Verify that hash is not included
            assert 'hash' not in metadata
            # Check that meta contains expected fields
            if metadata['meta']:
                # Common fields that might be present
                possible_fields = ['kategorie', 'aussteller', 'name', 'begründung', 'Autor']
                # At least one of these fields should be present if meta is not empty
                assert any(field in metadata['meta'] for field in possible_fields)
    
    # Check that full metadata is NOT included when not requested, but basic fields might be
    for doc in result_without_meta['documents']:
        assert 'metadata' not in doc  # No nested metadata object
        # But basic metadata fields might be present directly on the document
        # Only name is guaranteed, other fields depend on .pdf2md_index.json availability
        assert 'name' in doc
    
    # Test with non-existent project
    result_no_project = list_bidder_docs_json("NonExistentProject", "Demo2")
    assert isinstance(result_no_project, dict)
    assert 'error' in result_no_project
    assert result_no_project['error'] == "Project not found"
    
    # Test with non-existent bidder
    result_no_bidder = list_bidder_docs_json("Demoprojekt1", "NonExistentBidder")
    assert isinstance(result_no_bidder, dict)
    assert 'error' in result_no_bidder
    assert result_no_bidder['error'] == "Bidder not found in project"
    
    # Test default behavior (should include basic metadata fields but not full metadata)
    result_default = list_bidder_docs_json("Demoprojekt1", "Demo2")
    assert isinstance(result_default, dict)
    for doc in result_default['documents']:
        assert 'metadata' not in doc  # No nested metadata object
        assert 'name' in doc  # Name is always present
        # Basic metadata fields (kategorie, meta_name) might be present if available
        # but path, size, type should not be present by default
        assert 'path' not in doc
        assert 'size' not in doc
        assert 'type' not in doc


def test_list_project_docs_json():
    """Test the list_project_docs_json function."""
    from ofs.core import list_project_docs_json
    
    # Test with existing project (with metadata)
    result_with_meta = list_project_docs_json("Entrümpelung", include_metadata=True)
    assert isinstance(result_with_meta, dict)
    assert 'project' in result_with_meta
    assert 'documents' in result_with_meta
    assert 'total_documents' in result_with_meta
    assert result_with_meta['project'] == "Entrümpelung"
    assert isinstance(result_with_meta['documents'], list)
    assert isinstance(result_with_meta['total_documents'], int)
    
    # Test with existing project (without metadata)
    result_without_meta = list_project_docs_json("Entrümpelung", include_metadata=False)
    assert isinstance(result_without_meta, dict)
    assert 'project' in result_without_meta
    assert 'documents' in result_without_meta
    assert 'total_documents' in result_without_meta
    assert result_without_meta['project'] == "Entrümpelung"
    assert isinstance(result_without_meta['documents'], list)
    assert isinstance(result_without_meta['total_documents'], int)
    
    # Both results should have the same number of documents
    assert result_with_meta['total_documents'] == result_without_meta['total_documents']
    
    # Verify that only allowed document types are included in both cases
    for result in [result_with_meta, result_without_meta]:
        for doc in result['documents']:
            filename = doc['name'].lower()
            # Should not contain JSON or markdown files
            assert not filename.endswith('.json')
            assert not filename.endswith('.md')
            assert not filename.endswith('.markdown')
            # Should contain allowed extensions
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', 
                                '.tiff', '.tif', '.svg', '.webp', '.doc', '.docx', 
                                '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', 
                                '.odp', '.rtf', '.txt']
            assert any(filename.endswith(ext) for ext in allowed_extensions)
    
    # Check that metadata is included when requested
    for doc in result_with_meta['documents']:
        if 'metadata' in doc:
            metadata = doc['metadata']
            assert 'size' in metadata
            assert 'parsers' in metadata
            assert 'meta' in metadata
            # Verify that hash is not included
            assert 'hash' not in metadata
            # Check that meta contains expected fields
            if metadata['meta']:
                # Common fields that might be present
                possible_fields = ['kategorie', 'aussteller', 'name', 'begründung', 'Autor']
                # At least one of these fields should be present if meta is not empty
                assert any(field in metadata['meta'] for field in possible_fields)
    
    # Check that full metadata is NOT included when not requested, but basic fields might be
    for doc in result_without_meta['documents']:
        assert 'metadata' not in doc  # No nested metadata object
        # But basic metadata fields might be present directly on the document
        # Only name is guaranteed, other fields depend on .pdf2md_index.json availability
        assert 'name' in doc
    
    # Test with non-existent project
    result_no_project = list_project_docs_json("NonExistentProject")
    assert isinstance(result_no_project, dict)
    assert 'error' in result_no_project
    assert result_no_project['error'] == "Project not found"
    
    # Test default behavior (should include basic metadata fields but not full metadata)
    result_default = list_project_docs_json("Entrümpelung")
    assert isinstance(result_default, dict)
    for doc in result_default['documents']:
        assert 'metadata' not in doc  # No nested metadata object
        assert 'name' in doc  # Name is always present
        # Basic metadata fields (kategorie, meta_name) might be present if available
        # but path, size, type should not be present by default
        assert 'path' not in doc
        assert 'size' not in doc
        assert 'type' not in doc


def test_get_bidder_document_json():
    """Test the get_bidder_document_json function."""
    from ofs.core import get_bidder_document_json
    
    # Test with existing project, bidder, and document
    result = get_bidder_document_json("Entrümpelung", "Alpenglanz", "10formblatt-leistungsfaehigkeit.pdf")
    assert isinstance(result, dict)
    assert 'project' in result
    assert 'bidder' in result
    assert 'filename' in result
    assert result['project'] == "Entrümpelung"
    assert result['bidder'] == "Alpenglanz"
    assert result['filename'] == "10formblatt-leistungsfaehigkeit.pdf"
    
    # Should have file information
    assert 'path' in result
    assert 'size' in result
    assert 'type' in result
    assert 'exists' in result
    assert result['exists'] is True
    assert result['type'] == "file"
    
    # Should have metadata if available
    if 'metadata' in result:
        metadata = result['metadata']
        assert 'size' in metadata
        assert 'parsers' in metadata
        assert 'meta' in metadata
        # Verify that hash is not included
        assert 'hash' not in metadata
    
    # Should have basic metadata fields if available
    possible_fields = ['kategorie', 'meta_name', 'aussteller']
    # At least one of these fields might be present
    
    # Test with non-existent project
    result_no_project = get_bidder_document_json("NonExistentProject", "Alpenglanz", "10formblatt-leistungsfaehigkeit.pdf")
    assert isinstance(result_no_project, dict)
    assert 'error' in result_no_project
    assert result_no_project['error'] == "Project not found"
    
    # Test with non-existent bidder
    result_no_bidder = get_bidder_document_json("Entrümpelung", "NonExistentBidder", "10formblatt-leistungsfaehigkeit.pdf")
    assert isinstance(result_no_bidder, dict)
    assert 'error' in result_no_bidder
    assert result_no_bidder['error'] == "Bidder not found in project"
    
    # Test with non-existent document
    result_no_doc = get_bidder_document_json("Entrümpelung", "Alpenglanz", "nonexistent.pdf")
    assert isinstance(result_no_doc, dict)
    assert 'error' in result_no_doc
    assert result_no_doc['error'] == "Document not found"
    
    # Test with disallowed file type (JSON file)
    result_disallowed = get_bidder_document_json("Entrümpelung", "Alpenglanz", ".pdf2md_index.json")
    assert isinstance(result_disallowed, dict)
    assert 'error' in result_disallowed
    assert result_disallowed['error'] == "File type not allowed or not a document"


def test_config_integration():
    """Test that core functions work with config."""
    # This test ensures that the core functions can access configuration
    from ofs.config import get_base_dir
    base_dir = get_base_dir()
    assert isinstance(base_dir, str)
    assert len(base_dir) > 0