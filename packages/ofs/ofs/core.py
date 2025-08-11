"""
Core functionality for OFS (Opinionated Filesystem).

This module contains the main functions for accessing and navigating
the opinionated filesystem structure.
"""

import os
import json
import unicodedata
from pathlib import Path
from typing import Optional, List, Dict, Any

from .config import get_base_dir


def _load_pdf2md_index(directory_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load .pdf2md_index.json from a directory if it exists.

    Args:
        directory_path (Path): Path to the directory containing the index file

    Returns:
        Optional[Dict[str, Any]]: Parsed JSON data or None if file doesn't exist
    """
    index_file = directory_path / ".pdf2md_index.json"
    if index_file.exists():
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
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
    except PermissionError:
        # Skip directories we can't read
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

    projects = set()

    # Get projects from filesystem
    try:
        for item in base_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
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
            if dir_name:
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

    bidders = set()
    _collect_items_recursive(b_dir, bidders, search_depth=2)

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


def _collect_bidders_structured(b_dir: Path) -> Dict[str, Any]:
    """
    Collect bidders from B directory, distinguishing between directories and files.

    Args:
        b_dir (Path): The B directory to scan

    Returns:
        Dict[str, Any]: Structured data with bidders and files
    """
    # Reserved directory names that should be filtered out
    RESERVED_DIRS = {'md', '.pdf2md_index.json', 'A', 'B'}

    bidder_dirs = []
    all_files = []

    if not b_dir.exists():
        return {
            "bidder_directories": bidder_dirs,
            "all_files": all_files,
            "total_bidders": 0,
            "total_files": 0
        }

    # Scan filesystem
    try:
        for item in b_dir.iterdir():
            if item.name.startswith('.') or item.name.endswith('.meta.json'):
                continue

            normalized_name = unicodedata.normalize('NFC', item.name)

            if item.is_dir():
                # Filter out reserved directories
                if normalized_name not in RESERVED_DIRS:
                    bidder_dirs.append(normalized_name)

                    # Collect files from within this bidder directory
                    try:
                        for sub_item in item.iterdir():
                            if (sub_item.is_file() and
                                not sub_item.name.startswith('.') and
                                    not sub_item.name.endswith('.meta.json')):
                                file_name = unicodedata.normalize(
                                    'NFC', sub_item.name)
                                all_files.append(file_name)
                    except PermissionError:
                        pass
            elif item.is_file():
                # Files directly in B directory (rare but possible)
                if not normalized_name.startswith('.'):
                    all_files.append(normalized_name)
    except PermissionError:
        pass

    # Also check index file for additional entries
    index_data = _load_pdf2md_index(b_dir)
    if index_data:
        # Add directories from index
        for directory in index_data.get("directories", []):
            dir_name = directory.get("name", "")
            if dir_name:
                normalized_name = unicodedata.normalize('NFC', dir_name)
                if normalized_name not in RESERVED_DIRS and normalized_name not in bidder_dirs:
                    bidder_dirs.append(normalized_name)

        # Add files from index
        for file_info in index_data.get("files", []):
            file_name = file_info.get("name", "")
            if file_name and not file_name.endswith('.meta.json'):
                normalized_name = unicodedata.normalize('NFC', file_name)
                if not normalized_name.startswith('.') and normalized_name not in all_files:
                    all_files.append(normalized_name)

    return {
        "bidder_directories": sorted(bidder_dirs),
        "all_files": sorted(all_files),
        "total_bidders": len(bidder_dirs),
        "total_files": len(all_files)
    }


def list_bidder_docs_json(project_name: str, bidder_name: str, include_metadata: bool = False) -> Dict[str, Any]:
    """
    List all documents for a specific bidder in a project in JSON format.
    
    By default, returns a minimal view with document name and basic metadata fields
    (kategorie, meta_name) from .pdf2md_index.json files when available.
    
    With include_metadata=True, provides full document details including:
    - Complete file information (path, size, type)
    - Full metadata from .pdf2md_index.json files:
      - Document categorization (kategorie)
      - Document issuer (aussteller)
      - Document name (name)
      - Reasoning for categorization (begründung)
      - Parser information
      - File size and other metadata (excluding hash values)

    Args:
        project_name (str): Name of the project (AUSSCHREIBUNGNAME)
        bidder_name (str): Name of the bidder (BIETERNAME)
        include_metadata (bool): Whether to include full metadata and file details (default: False)

    Returns:
        Dict[str, Any]: JSON structure with documents for the bidder
        - Default: minimal view with name, kategorie, meta_name
        - With metadata: full document details and metadata
    """
    # Define allowed file extensions for documents
    allowed_extensions = {
        # PDF files
        '.pdf',
        # Image files
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.svg', '.webp',
        # Office documents
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp',
        # Other document formats
        '.rtf', '.txt'
    }

    # Extensions to exclude
    excluded_extensions = {
        '.json', '.md', '.markdown'
    }

    def is_allowed_document(filename):
        """Check if a file is an allowed document type."""
        _, ext = os.path.splitext(filename.lower())
        return ext in allowed_extensions and ext not in excluded_extensions

    base_dir = get_base_dir()
    base_path = Path(base_dir)

    # Find the project
    project_path = _search_in_directory(base_path, project_name)
    if not project_path:
        return {
            "project": project_name,
            "bidder": bidder_name,
            "documents": [],
            "total_documents": 0,
            "error": "Project not found"
        }

    project_dir = Path(project_path)
    b_dir = project_dir / "B"

    if not b_dir.exists():
        return {
            "project": project_name,
            "bidder": bidder_name,
            "documents": [],
            "total_documents": 0,
            "error": "No B directory found in project"
        }

    # Find the bidder directory
    bidder_path = _search_in_directory(b_dir, bidder_name, search_depth=2)
    if not bidder_path:
        return {
            "project": project_name,
            "bidder": bidder_name,
            "documents": [],
            "total_documents": 0,
            "error": "Bidder not found in project"
        }

    bidder_dir = Path(bidder_path)
    documents = []

    # Collect documents from filesystem
    try:
        for item in bidder_dir.iterdir():
            if (item.is_file() and
                not item.name.startswith('.') and
                not item.name.endswith('.meta.json') and
                    is_allowed_document(item.name)):
                normalized_name = unicodedata.normalize('NFC', item.name)
                doc_entry = {
                    "name": normalized_name,
                }
                if include_metadata:
                    doc_entry.update({
                        "path": str(item),
                        "size": item.stat().st_size if item.exists() else 0,
                        "type": "file"
                    })
                documents.append(doc_entry)
    except PermissionError:
        pass

    # Load metadata from .pdf2md_index.json - always load for basic metadata fields
    pdf2md_metadata = {}
    index_data = _load_pdf2md_index(bidder_dir)
    if index_data:
        # Create a mapping of filename to metadata
        for file_info in index_data.get("files", []):
            file_name = file_info.get("name", "")
            if file_name and is_allowed_document(file_name):
                # Extract metadata excluding hash
                if include_metadata:
                    # Full metadata when requested
                    metadata = {
                        "size": file_info.get("size", 0),
                        "parsers": file_info.get("parsers", {}),
                        "meta": file_info.get("meta", {})
                    }
                else:
                    # Basic metadata by default (only kategorie and name from meta)
                    meta_info = file_info.get("meta", {})
                    metadata = {}
                    if "kategorie" in meta_info:
                        metadata["kategorie"] = meta_info["kategorie"]
                    if "name" in meta_info:
                        metadata["meta_name"] = meta_info["name"]
                
                pdf2md_metadata[file_name] = metadata

                # Add files from the index that aren't already in our list
                if (not file_name.endswith('.meta.json')):
                    normalized_name = unicodedata.normalize(
                        'NFC', file_name)
                    # Check if we already have this file from filesystem scan
                    if not any(doc["name"] == normalized_name for doc in documents):
                        file_path = bidder_dir / file_name
                        doc_entry = {
                            "name": normalized_name,
                        }
                        if include_metadata:
                            doc_entry.update({
                                "path": str(file_path),
                                "size": file_info.get("size", 0),
                                "type": "file",
                                "metadata": metadata
                            })
                        else:
                            # Add basic metadata fields directly to document
                            doc_entry.update(metadata)
                        documents.append(doc_entry)

    # Enhance existing documents with metadata
    for doc in documents:
        if doc["name"] in pdf2md_metadata:
            if include_metadata and "metadata" not in doc:
                doc["metadata"] = pdf2md_metadata[doc["name"]]
            elif not include_metadata:
                # Add basic metadata fields directly to document
                doc.update(pdf2md_metadata[doc["name"]])

    # Sort documents by name
    documents.sort(key=lambda x: x["name"])

    return {
        "project": project_name,
        "bidder": bidder_name,
        "documents": documents,
        "total_documents": len(documents)
    }


def list_bidders_json(project_name: str) -> Dict[str, Any]:
    """
    List all bidders for a project in JSON format.

    Args:
        project_name (str): Name of the project

    Returns:
        Dict[str, Any]: JSON structure with bidders only (no files)
    """
    base_dir = get_base_dir()
    base_path = Path(base_dir)

    # Find the project
    project_path = _search_in_directory(base_path, project_name)
    if not project_path:
        return {
            "project": project_name,
            "bidders": [],
            "total_bidders": 0,
            "error": "Project not found"
        }

    project_dir = Path(project_path)
    b_dir = project_dir / "B"

    if not b_dir.exists():
        return {
            "project": project_name,
            "bidders": [],
            "total_bidders": 0,
            "error": "No B directory found in project"
        }

    # Get structured bidder data
    bidder_data = _collect_bidders_structured(b_dir)

    return {
        "project": project_name,
        "bidders": bidder_data["bidder_directories"],
        "total_bidders": bidder_data["total_bidders"]
    }


def list_project_docs_json(project_name: str, include_metadata: bool = False) -> Dict[str, Any]:
    """
    List all documents for a project from the A/ folder in JSON format.
    
    By default, returns a minimal view with document name and basic metadata fields
    (kategorie, meta_name) from .pdf2md_index.json files when available.
    
    With include_metadata=True, provides full document details including:
    - Complete file information (path, size, type)
    - Full metadata from .pdf2md_index.json files:
      - Document categorization (kategorie)
      - Document issuer (aussteller)
      - Document name (name)
      - Reasoning for categorization (begründung)
      - Parser information
      - File size and other metadata (excluding hash values)

    Args:
        project_name (str): Name of the project (AUSSCHREIBUNGNAME)
        include_metadata (bool): Whether to include full metadata and file details (default: False)

    Returns:
        Dict[str, Any]: JSON structure with documents for the project
        - Default: minimal view with name, kategorie, meta_name
        - With metadata: full document details and metadata
    """
    # Define allowed file extensions for documents
    allowed_extensions = {
        # PDF files
        '.pdf',
        # Image files
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.svg', '.webp',
        # Office documents
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp',
        # Other document formats
        '.rtf', '.txt'
    }

    # Extensions to exclude
    excluded_extensions = {
        '.json', '.md', '.markdown'
    }

    def is_allowed_document(filename):
        """Check if a file is an allowed document type."""
        _, ext = os.path.splitext(filename.lower())
        return ext in allowed_extensions and ext not in excluded_extensions

    base_dir = get_base_dir()
    base_path = Path(base_dir)

    # Find the project
    project_path = _search_in_directory(base_path, project_name)
    if not project_path:
        return {
            "project": project_name,
            "documents": [],
            "total_documents": 0,
            "error": "Project not found"
        }

    project_dir = Path(project_path)
    a_dir = project_dir / "A"

    if not a_dir.exists():
        return {
            "project": project_name,
            "documents": [],
            "total_documents": 0,
            "error": "No A directory found in project"
        }

    documents = []

    # Collect documents from filesystem
    try:
        for item in a_dir.iterdir():
            if (item.is_file() and
                not item.name.startswith('.') and
                not item.name.endswith('.meta.json') and
                    is_allowed_document(item.name)):
                normalized_name = unicodedata.normalize('NFC', item.name)
                doc_entry = {
                    "name": normalized_name,
                }
                if include_metadata:
                    doc_entry.update({
                        "path": str(item),
                        "size": item.stat().st_size if item.exists() else 0,
                        "type": "file"
                    })
                documents.append(doc_entry)
    except PermissionError:
        pass

    # Load metadata from .pdf2md_index.json - always load for basic metadata fields
    pdf2md_metadata = {}
    index_data = _load_pdf2md_index(a_dir)
    if index_data:
        # Create a mapping of filename to metadata
        for file_info in index_data.get("files", []):
            file_name = file_info.get("name", "")
            if file_name and is_allowed_document(file_name):
                # Extract metadata excluding hash
                if include_metadata:
                    # Full metadata when requested
                    metadata = {
                        "size": file_info.get("size", 0),
                        "parsers": file_info.get("parsers", {}),
                        "meta": file_info.get("meta", {})
                    }
                else:
                    # Basic metadata by default (only kategorie and name from meta)
                    meta_info = file_info.get("meta", {})
                    metadata = {}
                    if "kategorie" in meta_info:
                        metadata["kategorie"] = meta_info["kategorie"]
                    if "name" in meta_info:
                        metadata["meta_name"] = meta_info["name"]
                
                pdf2md_metadata[file_name] = metadata

                # Add files from the index that aren't already in our list
                if (not file_name.endswith('.meta.json')):
                    normalized_name = unicodedata.normalize(
                        'NFC', file_name)
                    # Check if we already have this file from filesystem scan
                    if not any(doc["name"] == normalized_name for doc in documents):
                        file_path = a_dir / file_name
                        doc_entry = {
                            "name": normalized_name,
                        }
                        if include_metadata:
                            doc_entry.update({
                                "path": str(file_path),
                                "size": file_info.get("size", 0),
                                "type": "file",
                                "metadata": metadata
                            })
                        else:
                            # Add basic metadata fields directly to document
                            doc_entry.update(metadata)
                        documents.append(doc_entry)

    # Enhance existing documents with metadata
    for doc in documents:
        if doc["name"] in pdf2md_metadata:
            if include_metadata and "metadata" not in doc:
                doc["metadata"] = pdf2md_metadata[doc["name"]]
            elif not include_metadata:
                # Add basic metadata fields directly to document
                doc.update(pdf2md_metadata[doc["name"]])

    # Sort documents by name
    documents.sort(key=lambda x: x["name"])

    return {
        "project": project_name,
        "documents": documents,
        "total_documents": len(documents)
    }


def get_bidder_document_json(project_name: str, bidder_name: str, filename: str) -> Dict[str, Any]:
    """
    Get detailed information for a specific document in a bidder's directory.
    
    This function provides comprehensive information about a specific document including:
    - Complete file information (path, size, type, modification time)
    - Full metadata from .pdf2md_index.json files:
      - Document categorization (kategorie)
      - Document issuer (aussteller)
      - Document name (name)
      - Reasoning for categorization (begründung)
      - Parser information
      - File size and other metadata (excluding hash values)

    Args:
        project_name (str): Name of the project (AUSSCHREIBUNGNAME)
        bidder_name (str): Name of the bidder (BIETERNAME)
        filename (str): Name of the specific document file

    Returns:
        Dict[str, Any]: JSON structure with detailed document information
    """
    # Define allowed file extensions for documents
    allowed_extensions = {
        # PDF files
        '.pdf',
        # Image files
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.svg', '.webp',
        # Office documents
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp',
        # Other document formats
        '.rtf', '.txt'
    }

    # Extensions to exclude
    excluded_extensions = {
        '.json', '.md', '.markdown'
    }

    def is_allowed_document(filename):
        """Check if a file is an allowed document type."""
        _, ext = os.path.splitext(filename.lower())
        return ext in allowed_extensions and ext not in excluded_extensions

    # Check if the filename is an allowed document type
    if not is_allowed_document(filename):
        return {
            "project": project_name,
            "bidder": bidder_name,
            "filename": filename,
            "error": "File type not allowed or not a document"
        }

    base_dir = get_base_dir()
    base_path = Path(base_dir)

    # Find the project
    project_path = _search_in_directory(base_path, project_name)
    if not project_path:
        return {
            "project": project_name,
            "bidder": bidder_name,
            "filename": filename,
            "error": "Project not found"
        }

    # Find the bidder within the project
    bidder_path = find_bidder_in_project(project_name, bidder_name)
    if not bidder_path:
        return {
            "project": project_name,
            "bidder": bidder_name,
            "filename": filename,
            "error": "Bidder not found in project"
        }

    bidder_dir = Path(bidder_path)
    file_path = bidder_dir / filename

    # Check if the file exists
    if not file_path.exists():
        return {
            "project": project_name,
            "bidder": bidder_name,
            "filename": filename,
            "error": "Document not found"
        }

    # Get basic file information
    try:
        file_stat = file_path.stat()
        normalized_name = unicodedata.normalize('NFC', filename)
        
        document_info = {
            "project": project_name,
            "bidder": bidder_name,
            "filename": normalized_name,
            "path": str(file_path),
            "size": file_stat.st_size,
            "type": "file",
            "modified": file_stat.st_mtime,
            "exists": True
        }
    except (OSError, PermissionError) as e:
        return {
            "project": project_name,
            "bidder": bidder_name,
            "filename": filename,
            "error": f"Cannot access file: {str(e)}"
        }

    # Load metadata from .pdf2md_index.json
    index_data = _load_pdf2md_index(bidder_dir)
    if index_data:
        # Find metadata for this specific file
        for file_info in index_data.get("files", []):
            if file_info.get("name", "") == filename:
                # Extract metadata excluding hash
                metadata = {
                    "size": file_info.get("size", 0),
                    "parsers": file_info.get("parsers", {}),
                    "meta": file_info.get("meta", {})
                }
                document_info["metadata"] = metadata
                
                # Also add basic metadata fields directly to document for convenience
                meta_info = file_info.get("meta", {})
                if "kategorie" in meta_info:
                    document_info["kategorie"] = meta_info["kategorie"]
                if "name" in meta_info:
                    document_info["meta_name"] = meta_info["name"]
                if "aussteller" in meta_info:
                    document_info["aussteller"] = meta_info["aussteller"]
                break

    return document_info
