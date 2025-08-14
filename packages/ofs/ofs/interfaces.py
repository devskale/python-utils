"""Interfaces and protocols for OFS dependency injection.

This module defines the abstract interfaces and protocols that enable
proper dependency injection throughout the OFS package.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol, Dict, Any, Optional, List


class ConfigProvider(Protocol):
    """Protocol for configuration providers.
    
    This protocol defines the interface that all configuration providers
    must implement to be compatible with the OFS dependency injection system.
    """
    
    def get_base_dir(self) -> str:
        """Get the base directory for OFS operations.
        
        Returns:
            str: The base directory path
        """
        ...
    
    def get_index_file(self) -> str:
        """Get the index file name.
        
        Returns:
            str: The index file name
        """
        ...
    
    def get_metadata_suffix(self) -> str:
        """Get the metadata file suffix.
        
        Returns:
            str: The metadata file suffix
        """
        ...
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Any: Configuration value
        """
        ...


class IndexManager(ABC):
    """Abstract base class for index management.
    
    This class defines the interface for all index management implementations
    and provides dependency injection for configuration.
    """
    
    def __init__(self, config: ConfigProvider):
        """Initialize the index manager with configuration.
        
        Args:
            config: Configuration provider instance
        """
        self.config = config
    
    @abstractmethod
    def load_index(self, directory: Path) -> Optional[Dict[str, Any]]:
        """Load index from directory.
        
        Args:
            directory: Directory to load index from
            
        Returns:
            Optional[Dict[str, Any]]: Index data or None if not found
        """
        pass
    
    @abstractmethod
    def create_index(self, directory: Path) -> bool:
        """Create index for directory.
        
        Args:
            directory: Directory to create index for
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def update_index(self, directory: Path) -> bool:
        """Update existing index for directory.
        
        Args:
            directory: Directory to update index for
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def clear_index(self, directory: Path) -> bool:
        """Clear index for directory.
        
        Args:
            directory: Directory to clear index for
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass


class PathResolver(ABC):
    """Abstract base class for path resolution.
    
    This class defines the interface for path resolution implementations
    and provides dependency injection for configuration.
    """
    
    def __init__(self, config: ConfigProvider):
        """Initialize the path resolver with configuration.
        
        Args:
            config: Configuration provider instance
        """
        self.config = config
    
    @abstractmethod
    def get_path(self, name: str) -> Optional[str]:
        """Resolve a name to its filesystem path.
        
        Args:
            name: Name to resolve (project or bidder)
            
        Returns:
            Optional[str]: Resolved path or None if not found
        """
        pass
    
    @abstractmethod
    def list_projects(self) -> List[str]:
        """List all available projects.
        
        Returns:
            List[str]: List of project names
        """
        pass
    
    @abstractmethod
    def list_bidders(self, project_name: str) -> List[str]:
        """List bidders for a project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            List[str]: List of bidder names
        """
        pass


class DocumentManager(ABC):
    """Abstract base class for document management.
    
    This class defines the interface for document management implementations
    and provides dependency injection for configuration.
    """
    
    def __init__(self, config: ConfigProvider, path_resolver: PathResolver):
        """Initialize the document manager with dependencies.
        
        Args:
            config: Configuration provider instance
            path_resolver: Path resolver instance
        """
        self.config = config
        self.path_resolver = path_resolver
    
    @abstractmethod
    def list_documents(self, target: str) -> List[Dict[str, Any]]:
        """List documents for a target (project or bidder).
        
        Args:
            target: Target identifier (project@bidder or project)
            
        Returns:
            List[Dict[str, Any]]: List of document metadata
        """
        pass
    
    @abstractmethod
    def read_document(self, document_id: str) -> Optional[str]:
        """Read document content.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Optional[str]: Document content or None if not found
        """
        pass


class TreeGenerator(ABC):
    """Abstract base class for tree structure generation.
    
    This class defines the interface for tree generation implementations
    and provides dependency injection for configuration.
    """
    
    def __init__(self, config: ConfigProvider):
        """Initialize the tree generator with configuration.
        
        Args:
            config: Configuration provider instance
        """
        self.config = config
    
    @abstractmethod
    def generate_tree(self, directories_only: bool = False) -> str:
        """Generate tree structure representation.
        
        Args:
            directories_only: Whether to show only directories
            
        Returns:
            str: Tree structure as string
        """
        pass


class KriterienManager(ABC):
    """Abstract base class for criteria management.
    
    This class defines the interface for criteria management implementations
    and provides dependency injection for configuration.
    """
    
    def __init__(self, config: ConfigProvider, path_resolver: PathResolver):
        """Initialize the criteria manager with dependencies.
        
        Args:
            config: Configuration provider instance
            path_resolver: Path resolver instance
        """
        self.config = config
        self.path_resolver = path_resolver
    
    @abstractmethod
    def load_kriterien(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Load criteria for a project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Optional[Dict[str, Any]]: Criteria data or None if not found
        """
        pass
    
    @abstractmethod
    def get_kriterien_population(self, project_name: str) -> Dict[str, Any]:
        """Get criteria population data.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Dict[str, Any]: Population data
        """
        pass
    
    @abstractmethod
    def build_kriterien_tree(self, project_name: str) -> Dict[str, Any]:
        """Build criteria tree structure.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Dict[str, Any]: Tree structure data
        """
        pass