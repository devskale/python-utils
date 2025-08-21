"""
OFS (Opinionated Filesystem) Package

A Python package for accessing and editing an opinionated filesystem
suited to handle tender documentation with rich options for indexes
and metadata sidecar files.
"""

# Legacy imports for backward compatibility
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
    get_project_document_json,
    read_doc,
    generate_tree_structure,
    print_tree_structure,
    get_kriterien_pop_json,
    get_kriterien_tree_json,
    get_kriterien_tag_json,
)
from .config import get_config, get_base_dir

# New dependency injection components
from .interfaces import (
    ConfigProvider,
    IndexManager,
    PathResolver,
    DocumentManager,
    TreeGenerator,
    KriterienManager,
)
from .api import (
    get_path_info,
    list_items,
    list_projects as api_list_projects,
    list_bidders_for_project,
    find_bidder,
    docs_list,
    read_document,
    kriterien_pop,
    kriterien_sync,
    kriterien_sync_all,
    kriterien_audit_event,
)
from .index import (
    create_index,
    update_index,
    clear_index,
    print_index_stats,
    generate_un_items_list,
)

# Kriterien Sync / Audit API (mirrors kriterien-sync & kriterien-audit CLI)
from .kriterien_sync import (
    SourceKriterium,
    SyncStats,
    load_kriterien_source,
    load_or_init_audit,
    reconcile_create,
    reconcile_full,
    write_audit_if_changed,
    append_event,
    derive_zustand,
)

__version__ = "0.1.1"
__all__ = [
    # Legacy functions
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
    "get_project_document_json",
    "read_doc",
    # Tree
    "generate_tree_structure",
    "print_tree_structure",
    # Kriterien JSON helpers
    "get_kriterien_pop_json",
    "get_kriterien_tree_json",
    "get_kriterien_tag_json",
    "get_kriterien_pop_json_bidder",
    "get_config",
    "get_base_dir",
    # Interfaces
    "ConfigProvider",
    "IndexManager",
    "PathResolver",
    "DocumentManager",
    "TreeGenerator",
    "KriterienManager",
    # Container
    "DIContainer",
    "OFSContainer",
    "get_container",
    "set_container",
    "reset_container",
    # Services
    "OFSService",
    "get_ofs_service",
    "set_ofs_service",
    "reset_ofs_service",
    # Implementations
    "DefaultIndexManager",
    "DefaultPathResolver",
    "DefaultDocumentManager",
    "DefaultTreeGenerator",
    "DefaultKriterienManager",
    # Index functions
    "create_index",
    "update_index",
    "clear_index",
    "print_index_stats",
    "generate_un_items_list",
    # Kriterien Sync / Audit API
    "SourceKriterium",
    "SyncStats",
    "load_kriterien_source",
    "load_or_init_audit",
    "reconcile_create",
    "reconcile_full",
    "write_audit_if_changed",
    "append_event",
    "derive_zustand",
    "kriterien_sync_all",
]
