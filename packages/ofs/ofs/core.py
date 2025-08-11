"""
Core functionality for OFS (Opinionated Filesystem).

This module aggregates functionality from the decomposed modules
to maintain backward compatibility.
"""

# Import from paths module
from .paths import (
    get_path,
    get_ofs_root,
    list_ofs_items,
    find_bidder_in_project,
    list_projects,
    list_bidders,
    get_paths_json,
    list_projects_json,
    _load_pdf2md_index,
    _search_in_directory,
    _collect_items_recursive,
    _search_all_paths,
    _determine_path_type,
)

# Import from docs module
from .docs import (
    list_bidder_docs_json,
    list_bidders_json,
    list_project_docs_json,
    get_bidder_document_json,
    read_doc,
    _select_parser,
    _collect_bidders_structured,
)

# Import from tree module
from .tree import (
    generate_tree_structure,
    print_tree_structure,
    _get_documents_from_directory,
)

# Re-export all functions for backward compatibility
__all__ = [
    # Path functions
    "get_path",
    "get_ofs_root", 
    "list_ofs_items",
    "find_bidder_in_project",
    "list_projects",
    "list_bidders",
    "get_paths_json",
    "list_projects_json",
    
    # Document functions
    "list_bidder_docs_json",
    "list_bidders_json",
    "list_project_docs_json", 
    "get_bidder_document_json",
    "read_doc",
    
    # Tree functions
    "generate_tree_structure",
    "print_tree_structure",
    
    # Private functions (for internal use)
    "_load_pdf2md_index",
    "_search_in_directory",
    "_collect_items_recursive",
    "_search_all_paths", 
    "_determine_path_type",
    "_select_parser",
    "_collect_bidders_structured",
    "_get_documents_from_directory",
]
