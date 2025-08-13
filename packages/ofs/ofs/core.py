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

# Import from kriterien module
from .kriterien import (
    load_kriterien,
    find_kriterien_file,
    get_unproven_kriterien,
    build_kriterien_tree,
    get_kriterien_by_tag,
    get_all_kriterien_tags,
    format_kriterien_list,
    format_kriterien_tree,
    format_kriterien_tags,
    format_kriterium_by_tag,
    get_kriterien_pop_json,
    get_kriterien_tree_json,
    get_kriterien_tag_json,
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

    # Kriterien functions
    "load_kriterien",
    "find_kriterien_file",
    "get_unproven_kriterien",
    "build_kriterien_tree",
    "get_kriterien_by_tag",
    "get_all_kriterien_tags",
    "format_kriterien_list",
    "format_kriterien_tree",
    "format_kriterien_tags",
    "format_kriterium_by_tag",
    "get_kriterien_pop_json",
    "get_kriterien_tree_json",
    "get_kriterien_tag_json",

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
