"""Service layer for OFS with dependency injection.

This module provides high-level services that use dependency injection
to coordinate between different OFS components.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

from .interfaces import (
    ConfigProvider,
    IndexManager,
    PathResolver,
    DocumentManager,
    TreeGenerator,
    KriterienManager
)
from .container import get_container


class OFSService:
    """High-level OFS service with dependency injection.
    
    This service provides a clean API for OFS operations while using
    dependency injection to manage component dependencies.
    """
    
    def __init__(
        self,
        config: Optional[ConfigProvider] = None,
        index_manager: Optional[IndexManager] = None,
        path_resolver: Optional[PathResolver] = None,
        document_manager: Optional[DocumentManager] = None,
        tree_generator: Optional[TreeGenerator] = None,
        kriterien_manager: Optional[KriterienManager] = None
    ):
        """Initialize the OFS service with optional dependency injection.
        
        Args:
            config: Configuration provider (uses container if None)
            index_manager: Index manager (uses container if None)
            path_resolver: Path resolver (uses container if None)
            document_manager: Document manager (uses container if None)
            tree_generator: Tree generator (uses container if None)
            kriterien_manager: Criteria manager (uses container if None)
        """
        container = get_container()
        
        self.config = config or container.get(ConfigProvider)
        self.index_manager = index_manager or container.get(IndexManager)
        self.path_resolver = path_resolver or container.get(PathResolver)
        self.document_manager = document_manager or container.get(DocumentManager)
        self.tree_generator = tree_generator or container.get(TreeGenerator)
        self.kriterien_manager = kriterien_manager or container.get(KriterienManager)
    
    # Path operations
    def get_path(self, name: str) -> Optional[str]:
        """Resolve a name to its filesystem path.
        
        Args:
            name: Name to resolve (project or bidder)
            
        Returns:
            Optional[str]: Resolved path or None if not found
        """
        return self.path_resolver.get_path(name)
    
    def list_projects(self) -> List[str]:
        """List all available projects.
        
        Returns:
            List[str]: List of project names
        """
        return self.path_resolver.list_projects()
    
    def list_bidders(self, project_name: str) -> List[str]:
        """List bidders for a project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            List[str]: List of bidder names
        """
        return self.path_resolver.list_bidders(project_name)
    
    # Document operations
    def list_documents(self, target: str) -> List[Dict[str, Any]]:
        """List documents for a target (project or bidder).
        
        Args:
            target: Target identifier (project@bidder or project)
            
        Returns:
            List[Dict[str, Any]]: List of document metadata
        """
        return self.document_manager.list_documents(target)
    
    def read_document(self, document_id: str) -> Optional[str]:
        """Read document content.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Optional[str]: Document content or None if not found
        """
        return self.document_manager.read_document(document_id)
    
    # Index operations
    def create_index(self, directory: str) -> bool:
        """Create index for directory.
        
        Args:
            directory: Directory to create index for
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.index_manager.create_index(Path(directory))
    
    def update_index(self, directory: str) -> bool:
        """Update existing index for directory.
        
        Args:
            directory: Directory to update index for
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.index_manager.update_index(Path(directory))
    
    def clear_index(self, directory: str) -> bool:
        """Clear index for directory.
        
        Args:
            directory: Directory to clear index for
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.index_manager.clear_index(Path(directory))
    
    def load_index(self, directory: str) -> Optional[Dict[str, Any]]:
        """Load index from directory.
        
        Args:
            directory: Directory to load index from
            
        Returns:
            Optional[Dict[str, Any]]: Index data or None if not found
        """
        return self.index_manager.load_index(Path(directory))
    
    # Tree operations
    def generate_tree(self, directories_only: bool = False) -> str:
        """Generate tree structure representation.
        
        Args:
            directories_only: Whether to show only directories
            
        Returns:
            str: Tree structure as string
        """
        return self.tree_generator.generate_tree(directories_only)
    
    # Criteria operations
    def load_kriterien(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Load criteria for a project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Optional[Dict[str, Any]]: Criteria data or None if not found
        """
        return self.kriterien_manager.load_kriterien(project_name)
    
    def get_kriterien_population(self, project_name: str) -> Dict[str, Any]:
        """Get criteria population data.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Dict[str, Any]: Population data
        """
        return self.kriterien_manager.get_kriterien_population(project_name)
    
    def build_kriterien_tree(self, project_name: str) -> Dict[str, Any]:
        """Build criteria tree structure.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Dict[str, Any]: Tree structure data
        """
        return self.kriterien_manager.build_kriterien_tree(project_name)


# Global service instance
_service: Optional[OFSService] = None


def get_ofs_service() -> OFSService:
    """Get the global OFS service instance.
    
    Returns:
        OFSService: The global service instance
    """
    global _service
    if _service is None:
        _service = OFSService()
    return _service


def set_ofs_service(service: OFSService) -> None:
    """Set the global OFS service instance.
    
    Args:
        service: The service instance to set as global
    """
    global _service
    _service = service


def reset_ofs_service() -> None:
    """Reset the global service instance."""
    global _service
    _service = None