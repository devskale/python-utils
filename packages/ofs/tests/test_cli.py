"""Tests for OFS CLI functionality."""

import pytest
import json
from unittest.mock import patch
from io import StringIO
import sys

from ofs.cli import create_parser, main


def test_create_parser():
    """Test that the argument parser is created correctly."""
    parser = create_parser()
    assert parser.prog == 'ofs'
    
    # Test that subcommands exist
    help_text = parser.format_help()
    assert 'get-path' in help_text
    assert 'list' in help_text
    assert 'list-projects' in help_text
    assert 'list-bidders' in help_text
    assert 'find-bidder' in help_text
    assert 'root' in help_text


def test_main_no_args():
    """Test main function with no arguments shows help."""
    with patch('sys.argv', ['ofs']):
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            main()
            # Should show help when no command is provided
            output = mock_stdout.getvalue()
            assert 'usage:' in output.lower()


def test_main_get_path():
    """Test main function with get-path command."""
    with patch('sys.argv', ['ofs', 'get-path', 'test_doc']):
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue().strip()
            # Should return valid JSON
            result = json.loads(output)
            assert result['name'] == 'test_doc'
            assert 'paths' in result
            assert 'count' in result


def test_main_get_path_project():
    """Test main function with get-path command for a project."""
    with patch('sys.argv', ['ofs', 'get-path', 'Demoprojekt1']):
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue().strip()
            # Should return valid JSON
            result = json.loads(output)
            assert result['name'] == 'Demoprojekt1'
            assert 'paths' in result
            assert 'count' in result


def test_main_list():
    """Test main function with list command."""
    with patch('sys.argv', ['ofs', 'list']):
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            # This should run successfully even if output is empty
            main()
            # Just verify it doesn't crash


def test_main_list_projects():
    """Test main function with list-projects command."""
    with patch('sys.argv', ['ofs', 'list-projects']):
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            main()
            # Should return valid JSON
            output = mock_stdout.getvalue().strip()
            result = json.loads(output)
            assert 'projects' in result
            assert 'count' in result
            assert isinstance(result['projects'], list)


def test_main_list_bidders():
    """Test main function with list-bidders command."""
    with patch('sys.argv', ['ofs', 'list-bidders', 'Demoprojekt1']):
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            main()
            # Should return valid JSON
            output = mock_stdout.getvalue().strip()
            result = json.loads(output)
            assert 'project' in result
            assert 'bidders' in result
            assert 'total_bidders' in result
            assert result['project'] == 'Demoprojekt1'
            assert isinstance(result['bidders'], list)
            # Should not include files anymore
            assert 'all_files' not in result
            assert 'total_files' not in result


def test_main_find_bidder():
    """Test main function with find-bidder command."""
    with patch('sys.argv', ['ofs', 'find-bidder', 'Demoprojekt1', 'Demo2']):
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            try:
                main()
                output = mock_stdout.getvalue().strip()
                # If successful, should contain the path
                if output and not output.startswith("Bidder"):
                    assert 'Demoprojekt1' in output
                    assert 'Demo2' in output
            except SystemExit as e:
                # Might exit with error if bidder not found
                pass


def test_main_list_docs():
    """Test main function with list-docs command (default behavior - without metadata)."""
    with patch('sys.argv', ['ofs', 'list-docs', 'Demoprojekt1@Demo2']):
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            try:
                main()
                # Should return valid JSON
                output = mock_stdout.getvalue().strip()
                result = json.loads(output)
                assert 'project' in result
                assert 'bidder' in result
                assert 'documents' in result
                assert 'total_documents' in result
                assert result['project'] == 'Demoprojekt1'
                assert result['bidder'] == 'Demo2'
                assert isinstance(result['documents'], list)
                assert isinstance(result['total_documents'], int)
                # By default, metadata should NOT be included
                for doc in result['documents']:
                    assert 'metadata' not in doc
            except SystemExit as e:
                # Might exit with error if project/bidder not found
                pass


def test_main_list_docs_with_meta():
    """Test main function with list-docs command with --meta flag."""
    with patch('sys.argv', ['ofs', 'list-docs', '--meta', 'Demoprojekt1@Demo2']):
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            try:
                main()
                # Should return valid JSON
                output = mock_stdout.getvalue().strip()
                result = json.loads(output)
                assert 'project' in result
                assert 'bidder' in result
                assert 'documents' in result
                assert 'total_documents' in result
                assert result['project'] == 'Demoprojekt1'
                assert result['bidder'] == 'Demo2'
                assert isinstance(result['documents'], list)
                assert isinstance(result['total_documents'], int)
                # With --meta flag, metadata should be included
                for doc in result['documents']:
                    if 'metadata' in doc:
                        # If metadata exists, verify its structure
                        metadata = doc['metadata']
                        assert 'size' in metadata
                        assert 'parsers' in metadata
                        assert 'meta' in metadata
            except SystemExit as e:
                # Might exit with error if project/bidder not found
                pass


def test_main_list_docs_without_meta():
    """Test main function with list-docs command without --meta flag (minimal output)."""
    with patch('sys.argv', ['ofs', 'list-docs', 'Demoprojekt1@Demo2']):
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            try:
                main()
                # Should return valid JSON
                output = mock_stdout.getvalue().strip()
                result = json.loads(output)
                assert 'project' in result
                assert 'bidder' in result
                assert 'documents' in result
                assert 'total_documents' in result
                assert result['project'] == 'Demoprojekt1'
                assert result['bidder'] == 'Demo2'
                assert isinstance(result['documents'], list)
                assert isinstance(result['total_documents'], int)
                # Without --meta flag, metadata should NOT be included
                for doc in result['documents']:
                    assert 'metadata' not in doc
            except SystemExit as e:
                # Might exit with error if project/bidder not found
                pass


def test_main_list_docs_invalid_format():
    """Test main function with list-docs command and invalid format."""
    with patch('sys.argv', ['ofs', 'list-docs', 'InvalidFormat']):
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            try:
                main()
                # Should not reach here
                assert False, "Expected SystemExit"
            except SystemExit as e:
                # Should exit with error
                assert e.code == 1
                error_output = mock_stderr.getvalue()
                assert "Invalid format" in error_output


def test_main_root():
    """Test main function with root command."""
    with patch('sys.argv', ['ofs', 'root']):
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue().strip()
            # Should return a non-empty path
            assert len(output) > 0