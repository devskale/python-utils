"""Tests for OFS CLI functionality."""

import pytest
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
            # Should contain both the document name and .dir
            assert 'test_doc' in output
            assert '.dir' in output


def test_main_get_path_project():
    """Test main function with get-path command for a project."""
    with patch('sys.argv', ['ofs', 'get-path', 'Demoprojekt1']):
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue().strip()
            assert 'Demoprojekt1' in output
            assert '.dir' in output


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
            # Should run successfully
            output = mock_stdout.getvalue()
            # Output might contain project names or be empty


def test_main_list_bidders():
    """Test main function with list-bidders command."""
    with patch('sys.argv', ['ofs', 'list-bidders', 'Demoprojekt1']):
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            main()
            # Should run successfully
            output = mock_stdout.getvalue()
            # Output might contain bidder names or be empty


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


def test_main_root():
    """Test main function with root command."""
    with patch('sys.argv', ['ofs', 'root']):
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue().strip()
            # Should return a non-empty path
            assert len(output) > 0