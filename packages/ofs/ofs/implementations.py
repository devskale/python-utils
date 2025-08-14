"""Concrete implementations of OFS interfaces.

This module provides the default implementations of the OFS interfaces,
wrapping existing functionality with proper dependency injection.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from .interfaces import (
    ConfigProvider,
    IndexManager,
    PathResolver,
    DocumentManager,
    TreeGenerator,
    KriterienManager
)


class DefaultIndexManager(IndexManager):
    """Default implementation of IndexManager.
    
    This implementation wraps the existing index functionality
    with proper dependency injection.
    """
    
    def load_index(self, directory: Path) -> Optional[Dict[str, Any]]:
        """Load index from directory.
        
        Args:
            directory: Directory to load index from
            
        Returns:
            Optional[Dict[str, Any]]: Index data or None if not found
        """
        index_file_name = self.config.get_index_file()
        index_file = directory / index_file_name
        
        if not index_file.exists():
            return None
        
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, PermissionError):
            return None
    
    def create_index(self, directory: Path) -> bool:
        """Create index for directory.
        
        Args:
            directory: Directory to create index for
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Import the existing create_index function
            from . import index
            index.create_index(str(directory))
            return True
        except Exception:
            return False
    
    def update_index(self, directory: Path) -> bool:
        """Update existing index for directory.
        
        Args:
            directory: Directory to update index for
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Import the existing update_index function
            from . import index
            index.update_index(str(directory))
            return True
        except Exception:
            return False
    
    def clear_index(self, directory: Path) -> bool:
        """Clear index for directory.
        
        Args:
            directory: Directory to clear index for
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Import the existing clear_index function
            from . import index
            index.clear_index(str(directory))
            return True
        except Exception:
            return False


class DefaultPathResolver(PathResolver):
    """Default implementation of PathResolver.
    
    This implementation wraps the existing path functionality
    with proper dependency injection.
    """
    
    def get_path(self, name: str) -> Optional[str]:
        """Resolve a name to its filesystem path.
        
        Args:
            name: Name to resolve (project or bidder)
            
        Returns:
            Optional[str]: Resolved path or None if not found
        """
        try:
            # Import the existing get_path function
            from . import paths
            return paths.get_path(name)
        except Exception:
            return None
    
    def list_projects(self) -> List[str]:
        """List all available projects.
        
        Returns:
            List[str]: List of project names
        """
        try:
            # Import the existing list_projects function
            from . import paths
            return paths.list_projects()
        except Exception:
            return []
    
    def list_bidders(self, project_name: str) -> List[str]:
        """List bidders for a project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            List[str]: List of bidder names
        """
        try:
            # Import the existing list_bidders function
            from . import paths
            return paths.list_bidders(project_name)
        except Exception:
            return []


class DefaultDocumentManager(DocumentManager):
    """Default implementation of DocumentManager.
    
    This implementation wraps the existing document functionality
    with proper dependency injection.
    """
    
    def list_documents(self, target: str) -> List[Dict[str, Any]]:
        """List documents for a target (project or bidder).
        
        Args:
            target: Target identifier (project@bidder or project)
            
        Returns:
            List[Dict[str, Any]]: List of document metadata
        """
        try:
            # Import the existing docs functions
            from . import docs
            
            if '@' in target:
                # Handle project@bidder format
                project, bidder = target.split('@', 1)
                result = docs.list_bidder_docs_json(project, bidder)
                return result.get('documents', [])
            else:
                # Handle project format
                result = docs.list_project_docs_json(target)
                return result.get('documents', [])
        except Exception:
            return []
    
    def read_document(self, document_id: str) -> Optional[str]:
        """Read document content.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Optional[str]: Document content or None if not found
        """
        try:
            # Import the existing read_doc function
            from . import docs
            return docs.read_doc(document_id)
        except Exception:
            return None


class DefaultTreeGenerator(TreeGenerator):
    """Default implementation of TreeGenerator.
    
    This implementation wraps the existing tree functionality
    with proper dependency injection.
    """
    
    def generate_tree(self, directories_only: bool = False) -> str:
        """Generate tree structure representation.
        
        Args:
            directories_only: Whether to show only directories
            
        Returns:
            str: Tree structure as string
        """
        try:
            # Import the existing tree functions
            from . import tree
            
            base_dir = Path(self.config.get_base_dir())
            tree_data = tree.generate_tree_structure(str(base_dir), directories_only)
            return tree.print_tree_structure(tree_data)
        except Exception:
            return "Error generating tree structure"


class DefaultKriterienManager(KriterienManager):
    """Default implementation of KriterienManager.
    
    This implementation wraps the existing criteria functionality
    with proper dependency injection.
    """
    
    def load_kriterien(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Load criteria for a project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Optional[Dict[str, Any]]: Criteria data or None if not found
        """
        try:
            # Import the existing kriterien functions
            from . import kriterien
            return kriterien.load_kriterien(project_name)
        except Exception:
            return None
    
    def get_kriterien_population(self, project_name: str) -> Dict[str, Any]:
        """Get criteria population data.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Dict[str, Any]: Population data
        """
        try:
            # Import the existing kriterien functions
            from . import kriterien
            return kriterien.get_kriterien_pop_json(project_name)
        except Exception:
            return {'error': 'Failed to load criteria population data'}
    
    def build_kriterien_tree(self, project_name: str) -> Dict[str, Any]:
        """Build criteria tree structure.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Dict[str, Any]: Tree structure data
        """
        try:
            # Import the existing kriterien functions
            from . import kriterien
            return kriterien.get_kriterien_tree_json(project_name)
        except Exception:
            return {'error': 'Failed to build criteria tree'}