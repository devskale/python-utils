"""
Tree structure generation and visualization for OFS.

This module contains functions for:
- Generating a structured representation of the OFS directory tree
- Pretty-printing the tree to a string
"""

from pathlib import Path
from typing import Dict, Any, List, Optional

from .config import get_base_dir


RESERVED_DIRS = {"md", "archive"}
RESERVED_FILE_EXTENSIONS = {".json", ".md"}


def _get_documents_from_directory(directory: Path, reserved_dirs: set = None) -> List[Dict[str, Any]]:
    """
    Helper function to get documents from a directory, excluding reserved dirs/files.
    """
    if reserved_dirs is None:
        reserved_dirs = RESERVED_DIRS

    documents: List[Dict[str, Any]] = []
    try:
        if not directory.exists():
            return documents
        
        if not directory.is_dir():
            return documents
            
        for item in directory.iterdir():
            # Skip hidden files and reserved file types
            if item.name.startswith('.'):
                continue
            if item.is_file() and item.suffix.lower() in RESERVED_FILE_EXTENSIONS:
                continue
            if item.is_file():
                try:
                    documents.append({
                        "name": item.name,
                        "path": str(item),
                        "type": item.suffix.lower(),
                        "size": item.stat().st_size
                    })
                except (OSError, PermissionError):
                    # Skip files that can't be accessed
                    continue
    except (OSError, PermissionError):
        pass

    return documents


def generate_tree_structure(directories_only: bool = False) -> Dict[str, Any]:
    """
    Generate a structured tree representation of projects, bidders, and documents.

    Args:
        directories_only (bool): If True, only include directories in the tree

    Returns:
        Dict[str, Any]: Nested dictionary representing the tree structure
    """
    base_dir = get_base_dir()
    base_path = Path(base_dir)

    tree: Dict[str, Any] = {
        "base_dir": base_dir,
        "projects": []
    }

    if not base_path.exists():
        return tree

    try:
        items = list(base_path.iterdir())
    except (OSError, PermissionError):
        return tree
        
    try:
        for project_dir in items:
            if not project_dir.is_dir() or project_dir.name.startswith('.') or project_dir.name in RESERVED_DIRS:
                continue

            project_node: Dict[str, Any] = {
                "name": project_dir.name,
                "path": str(project_dir),
                "directories": [],
            }

            # Add A directory
            a_dir = project_dir / "A"
            if a_dir.exists() and a_dir.is_dir():
                a_node: Dict[str, Any] = {
                    "name": "A",
                    "path": str(a_dir),
                    "documents": [] if not directories_only else None,
                }
                if not directories_only:
                    a_node["documents"] = _get_documents_from_directory(a_dir)
                project_node["directories"].append(a_node)

            # Add B directory and bidders
            b_dir = project_dir / "B"
            if b_dir.exists() and b_dir.is_dir():
                b_node: Dict[str, Any] = {
                    "name": "B",
                    "path": str(b_dir),
                    "bidders": []
                }

                try:
                    for bidder_dir in b_dir.iterdir():
                        if not bidder_dir.is_dir() or bidder_dir.name.startswith('.') or bidder_dir.name in RESERVED_DIRS:
                            continue

                        bidder_node: Dict[str, Any] = {
                            "name": bidder_dir.name,
                            "path": str(bidder_dir),
                            "documents": [] if not directories_only else None,
                        }
                        if not directories_only:
                            bidder_node["documents"] = _get_documents_from_directory(bidder_dir)

                        b_node["bidders"].append(bidder_node)
                except PermissionError:
                    pass

                project_node["directories"].append(b_node)

            tree["projects"].append(project_node)
    except PermissionError:
        pass

    return tree


def print_tree_structure(directories_only: bool = False) -> str:
    """
    Format the tree structure as a string suitable for console output.
    """
    tree = generate_tree_structure(directories_only=directories_only)

    lines: List[str] = []
    base_dir = tree.get("base_dir", "")
    lines.append(f"{base_dir}/")

    for project in tree.get("projects", []):
        lines.append(f"├── {project['name']}/")
        for directory in project.get("directories", []):
            if directory["name"] == "A":
                lines.append(f"│   ├── A/")
                if not directories_only:
                    for doc in directory.get("documents", []) or []:
                        lines.append(f"│   │   ├── {doc['name']}")
            elif directory["name"] == "B":
                lines.append(f"│   └── B/")
                for bidder in directory.get("bidders", []):
                    lines.append(f"│       ├── {bidder['name']}/")
                    if not directories_only:
                        for doc in bidder.get("documents", []) or []:
                            lines.append(f"│       │   ├── {doc['name']}")

    return "\n".join(lines)