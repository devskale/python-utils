"""
OFS (Opinionated Filesystem) Package

A Python package for accessing and editing an opinionated filesystem
suited to handle tender documentation with rich options for indexes
and metadata sidecar files.
"""

from .core import (
    get_path,
    get_ofs_root,
    list_ofs_items,
    list_projects,
    list_bidders,
    find_bidder_in_project,
    list_bidder_docs_json,
    list_project_docs_json,
    get_paths_json,
    list_projects_json,
    list_bidders_json,
    get_bidder_document_json,
    read_doc,
)
from .config import get_config, get_base_dir

__version__ = "0.1.0"
__all__ = [
    "get_path",
    "get_ofs_root",
    "list_ofs_items",
    "list_projects",
    "list_bidders",
    "find_bidder_in_project",
    "list_bidder_docs_json",
    "list_project_docs_json",
    "get_paths_json",
    "list_projects_json",
    "list_bidders_json",
    "get_bidder_document_json",
    "read_doc",
    "get_config",
    "get_base_dir",
]