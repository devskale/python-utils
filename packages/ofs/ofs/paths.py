"""
Path resolution and navigation functionality for OFS (Opinionated Filesystem).

This module contains functions for:
- Path resolution and searching
- Project and bidder discovery
- Directory navigation and item listing
"""

import os
import json
import unicodedata
from pathlib import Path
from typing import Optional, List, Dict, Any

from .config import get_base_dir, get_config


def _load_pdf2md_index(directory_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load .pdf2md_index.json from a directory if it exists.

    Args:
        directory_path (Path): Path to the directory containing the index file

    Returns:
        Optional[Dict[str, Any]]: Parsed JSON data or None if file doesn't exist
    """
    config = get_config()
    index_file_name = config.get('INDEX_FILE', 'ofs.index.json')
    index_file = directory_path / index_file_name
    if index_file.exists():
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, PermissionError) as e:
            # Silently ignore malformed or unreadable index files
            pass
    return None


def _search_in_directory(base_path: Path, name: str, search_depth: int = 3) -> Optional[str]:
    """
    Search for a name in directory structure and index files.

    Args:
        base_path (Path): Base directory to search in
        name (str): Name to search for
        search_depth (int): Maximum depth to search (prevents infinite recursion)

    Returns:
        Optional[str]: Path to the found item or None if not found
    """
    if search_depth <= 0 or not base_path.exists():
        return None

    # Check if the name exists as a direct subdirectory
    direct_path = base_path / name
    if direct_path.exists():
        return str(direct_path)

    # Load and check the index file in current directory
    index_data = _load_pdf2md_index(base_path)
    if index_data:
        # Check directories in index
        for directory in index_data.get("directories", []):
            dir_name = directory.get("name", "")
            if dir_name == name:
                found_path = base_path / dir_name
                if found_path.exists():
                    return str(found_path)

        # Check files in index
        for file_info in index_data.get("files", []):
            file_name = file_info.get("name", "")
            if file_name == name:
                found_path = base_path / file_name
                if found_path.exists():
                    return str(found_path)

    # Recursively search in subdirectories
    try:
        for item in base_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                result = _search_in_directory(item, name, search_depth - 1)
                if result:
                    return result
    except (PermissionError, OSError, UnicodeDecodeError):
        # Skip directories we can't read or have encoding issues
        pass

    return None


def get_path(name: str) -> str:
    """
    Get the path for a given name in the OFS structure.

    Searches for AUSSCHREIBUNGNAME (project names) and BIETERNAME (bidder names)
    by traversing directories and consulting .pdf2md_index.json files.

    The function searches in the following order:
    1. Direct match in BASE_DIR
    2. Names listed in .pdf2md_index.json files
    3. Recursive search through subdirectories

    Args:
        name (str): The name to resolve to a path (AUSSCHREIBUNGNAME or BIETERNAME)

    Returns:
        str: The resolved path within the BASE_DIR, or a constructed path if not found

    Example:
        >>> get_path("2025-04 Lampen")  # AUSSCHREIBUNGNAME
        '.dir/2025-04 Lampen'
        >>> get_path("Lampion GmbH")    # BIETERNAME
        '.dir/2025-04 Lampen/B/Lampion GmbH'
    """
    base_dir = get_base_dir()
    base_path = Path(base_dir)

    # Ensure the base directory exists
    if not base_path.exists():
        base_path.mkdir(parents=True, exist_ok=True)

    # Search for the name in the OFS structure
    found_path = _search_in_directory(base_path, name)

    if found_path:
        return found_path

    # If not found, return a constructed path as fallback
    # This maintains backward compatibility with the previous behavior
    return str(base_path / name)


def get_ofs_root() -> Optional[str]:
    """
    Find the root directory of the current OFS structure.

    This function searches upward from the current directory to find
    the OFS root (identified by the BASE_DIR or config files).

    Returns:
        Optional[str]: Path to OFS root directory, or None if not found
    """
    current_dir = Path.cwd()
    base_dir = get_base_dir()

    # Check if BASE_DIR exists in current directory
    if (current_dir / base_dir).exists():
        return str(current_dir)

    # Search upward for OFS root
    for parent in current_dir.parents:
        if (parent / base_dir).exists():
            return str(parent)
        # Also check for config files
        if (parent / "ofs.config.json").exists():
            return str(parent)

    # If not found, return current directory as default
    return str(current_dir)


def _collect_items_recursive(base_path: Path, collected_items: set, search_depth: int = 3) -> None:
    """
    Recursively collect all items from directories and index files.

    Args:
        base_path (Path): Directory to search in
        collected_items (set): Set to collect unique item names
        search_depth (int): Maximum depth to search
    """
    if search_depth <= 0 or not base_path.exists():
        return

    # Add items from filesystem
    try:
        for item in base_path.iterdir():
            if not item.name.startswith('.') and not item.name.endswith('.meta.json'):
                # Normalize Unicode to handle different encodings of the same characters
                normalized_name = unicodedata.normalize('NFC', item.name)
                collected_items.add(normalized_name)

                # Recursively search subdirectories
                if item.is_dir():
                    _collect_items_recursive(
                        item, collected_items, search_depth - 1)
    except PermissionError:
        pass

    # Add items from index file
    index_data = _load_pdf2md_index(base_path)
    if index_data:
        # Add directories from index
        for directory in index_data.get("directories", []):
            dir_name = directory.get("name", "")
            if dir_name:
                # Normalize Unicode to handle different encodings of the same characters
                normalized_name = unicodedata.normalize('NFC', dir_name)
                collected_items.add(normalized_name)

        # Add files from index
        for file_info in index_data.get("files", []):
            file_name = file_info.get("name", "")
            if file_name and not file_name.endswith('.meta.json'):
                # Normalize Unicode to handle different encodings of the same characters
                normalized_name = unicodedata.normalize('NFC', file_name)
                collected_items.add(normalized_name)


def list_ofs_items() -> list[str]:
    """
    List all items available in the current OFS structure.

    Scans the BASE_DIR and all .pdf2md_index.json files for available 
    files and directories, including AUSSCHREIBUNGNAME and BIETERNAME.

    Returns:
        list[str]: List of available item names in the OFS
    """
    base_dir = get_base_dir()
    base_path = Path(base_dir)

    if not base_path.exists():
        return []

    items = set()
    _collect_items_recursive(base_path, items)

    return sorted(list(items))


def find_bidder_in_project(project_name: str, bidder_name: str) -> Optional[str]:
    """
    Find a specific bidder within a project.

    Args:
        project_name (str): Name of the project (AUSSCHREIBUNGNAME)
        bidder_name (str): Name of the bidder (BIETERNAME)

    Returns:
        Optional[str]: Path to the bidder directory or None if not found
    """
    base_dir = get_base_dir()
    base_path = Path(base_dir)

    # First find the project
    project_path = _search_in_directory(base_path, project_name)
    if not project_path:
        return None

    project_dir = Path(project_path)

    # Look for bidder in the B/ subdirectory
    b_dir = project_dir / "B"
    if b_dir.exists():
        bidder_path = _search_in_directory(b_dir, bidder_name, search_depth=2)
        if bidder_path:
            return bidder_path

    return None


def list_projects() -> list[str]:
    """
    List all project names (AUSSCHREIBUNGNAME) in the OFS structure.

    Returns:
        list[str]: List of project names
    """
    base_dir = get_base_dir()
    base_path = Path(base_dir)

    if not base_path.exists():
        return []

    # Reserved directories to exclude
    reserved_dirs = {"md", "archive"}
    projects = set()

    # Get projects from filesystem
    try:
        for item in base_path.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name not in reserved_dirs:
                # Normalize Unicode to handle different encodings of the same characters
                normalized_name = unicodedata.normalize('NFC', item.name)
                projects.add(normalized_name)
    except PermissionError:
        pass

    # Get projects from index file
    index_data = _load_pdf2md_index(base_path)
    if index_data:
        for directory in index_data.get("directories", []):
            dir_name = directory.get("name", "")
            if dir_name and dir_name not in reserved_dirs:
                # Normalize Unicode to handle different encodings of the same characters
                normalized_name = unicodedata.normalize('NFC', dir_name)
                projects.add(normalized_name)

    return sorted(list(projects))


def list_bidders(project_name: str) -> list[str]:
    """
    List all bidder names (BIETERNAME) within a specific project.

    Args:
        project_name (str): Name of the project (AUSSCHREIBUNGNAME)

    Returns:
        list[str]: List of bidder names in the project
    """
    base_dir = get_base_dir()
    base_path = Path(base_dir)

    # Find the project
    project_path = _search_in_directory(base_path, project_name)
    if not project_path:
        return []

    project_dir = Path(project_path)
    b_dir = project_dir / "B"

    if not b_dir.exists():
        return []

    # Reserved directories and file extensions to exclude
    reserved_dirs = {"md", "archive"}
    reserved_file_extensions = {".json", ".md"}
    
    bidders = set()
    
    # Only collect directories, not files
    try:
        for item in b_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name not in reserved_dirs:
                # Normalize Unicode to handle different encodings of the same characters
                normalized_name = unicodedata.normalize('NFC', item.name)
                bidders.add(normalized_name)
    except PermissionError:
        pass
    
    # Add bidders from index file
    index_data = _load_pdf2md_index(b_dir)
    if index_data:
        for directory in index_data.get("directories", []):
            dir_name = directory.get("name", "")
            if dir_name and dir_name not in reserved_dirs:
                # Normalize Unicode to handle different encodings of the same characters
                normalized_name = unicodedata.normalize('NFC', dir_name)
                bidders.add(normalized_name)

    return sorted(list(bidders))


def _search_all_paths(base_path: Path, name: str, search_depth: int = 3) -> List[Dict[str, str]]:
    """
    Search for all occurrences of a name in directory structure and index files.

    Args:
        base_path (Path): Base directory to search in
        name (str): Name to search for
        search_depth (int): Maximum depth to search

    Returns:
        List[Dict[str, str]]: List of dictionaries with 'path' and 'type' keys
    """
    results = []

    if search_depth <= 0 or not base_path.exists():
        return results

    # Check if the name exists as a direct subdirectory
    direct_path = base_path / name
    if direct_path.exists():
        # Determine type based on parent directory structure
        path_type = _determine_path_type(direct_path)
        results.append({
            "path": str(direct_path),
            "type": path_type
        })

    # Load and check the index file in current directory
    index_data = _load_pdf2md_index(base_path)
    if index_data:
        # Check directories in index
        for directory in index_data.get("directories", []):
            dir_name = directory.get("name", "")
            if dir_name == name:
                found_path = base_path / dir_name
                if found_path.exists():
                    path_type = _determine_path_type(found_path)
                    path_dict = {
                        "path": str(found_path),
                        "type": path_type
                    }
                    # Avoid duplicates
                    if path_dict not in results:
                        results.append(path_dict)

        # Check files in index
        for file_info in index_data.get("files", []):
            file_name = file_info.get("name", "")
            if file_name == name:
                found_path = base_path / file_name
                if found_path.exists():
                    path_type = _determine_path_type(found_path)
                    path_dict = {
                        "path": str(found_path),
                        "type": path_type
                    }
                    # Avoid duplicates
                    if path_dict not in results:
                        results.append(path_dict)

    # Recursively search in subdirectories
    try:
        for item in base_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                sub_results = _search_all_paths(item, name, search_depth - 1)
                for result in sub_results:
                    if result not in results:
                        results.append(result)
    except PermissionError:
        # Skip directories we can't read
        pass

    return results


def _determine_path_type(path: Path) -> str:
    """
    Determine the type of a path based on its location in the OFS structure.

    Args:
        path (Path): Path to analyze

    Returns:
        str: Type identifier ('A', 'B', 'project', 'file', or 'unknown')
    """
    path_parts = path.parts

    # Check if it's in an A/ directory
    if 'A' in path_parts:
        return 'A'

    # Check if it's in a B/ directory
    if 'B' in path_parts:
        return 'B'

    # Check if it's a project directory (direct child of base_dir)
    base_dir = get_base_dir()
    base_path = Path(base_dir)
    try:
        relative_path = path.relative_to(base_path)
        if len(relative_path.parts) == 1 and path.is_dir():
            return 'project'
    except ValueError:
        pass

    # Check if it's a file
    if path.is_file():
        return 'file'

    return 'unknown'


def get_paths_json(name: str) -> Dict[str, Any]:
    """
    Get all paths for a given name in JSON format.

    Args:
        name (str): The name to search for

    Returns:
        Dict[str, Any]: JSON structure with paths and metadata
    """
    base_dir = get_base_dir()
    base_path = Path(base_dir)

    # Ensure the base directory exists
    if not base_path.exists():
        base_path.mkdir(parents=True, exist_ok=True)
        return {
            "name": name,
            "paths": [],
            "count": 0
        }

    # Search for all occurrences of the name
    found_paths = _search_all_paths(base_path, name)

    return {
        "name": name,
        "paths": found_paths,
        "count": len(found_paths)
    }


def list_projects_json() -> Dict[str, Any]:
    """
    List all projects in JSON format.

    Returns:
        Dict[str, Any]: JSON structure with project list
    """
    projects = list_projects()

    return {
        "projects": projects,
        "count": len(projects)
    }