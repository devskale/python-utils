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
    read_doc,
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
from .container import (
    DIContainer,
    OFSContainer,
    get_container,
    set_container,
    reset_container,
)
from .services import (
    OFSService,
    get_ofs_service,
    set_ofs_service,
    reset_ofs_service,
)
from .implementations import (
    DefaultIndexManager,
    DefaultPathResolver,
    DefaultDocumentManager,
    DefaultTreeGenerator,
    DefaultKriterienManager,
)

__version__ = "0.1.0"
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
    "read_doc",
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
]
