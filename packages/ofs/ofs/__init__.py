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
    find_bidder_in_project,
    list_projects,
    list_bidders
)
from .config import get_config, get_base_dir

__version__ = "0.1.0"
__all__ = [
    "get_path", 
    "get_ofs_root", 
    "list_ofs_items",
    "find_bidder_in_project",
    "list_projects",
    "list_bidders",
    "get_config", 
    "get_base_dir"
]