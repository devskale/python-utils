"""Dependency injection container for OFS.

This module provides a simple dependency injection container that manages
the creation and wiring of OFS components.
"""

from typing import Dict, Any, TypeVar, Type, Callable, Optional
from .interfaces import (
    ConfigProvider,
    IndexManager,
    PathResolver,
    DocumentManager,
    TreeGenerator,
    KriterienManager
)

T = TypeVar('T')


class DIContainer:
    """Simple dependency injection container.
    
    This container manages the creation and lifecycle of OFS components,
    ensuring proper dependency injection throughout the application.
    """
    
    def __init__(self):
        """Initialize the dependency injection container."""
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a singleton service.
        
        Args:
            interface: The interface type
            implementation: The implementation type
        """
        key = interface.__name__
        self._factories[key] = lambda: implementation
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """Register a factory function for a service.
        
        Args:
            interface: The interface type
            factory: Factory function that creates the service
        """
        key = interface.__name__
        self._factories[key] = factory
    
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register a specific instance for a service.
        
        Args:
            interface: The interface type
            instance: The instance to register
        """
        key = interface.__name__
        self._singletons[key] = instance
    
    def get(self, interface: Type[T]) -> T:
        """Get a service instance.
        
        Args:
            interface: The interface type to get
            
        Returns:
            T: The service instance
            
        Raises:
            ValueError: If the service is not registered
        """
        key = interface.__name__
        
        # Check if we have a singleton instance
        if key in self._singletons:
            return self._singletons[key]
        
        # Check if we have a factory
        if key in self._factories:
            factory = self._factories[key]
            instance = factory()
            
            # Store as singleton for future requests
            self._singletons[key] = instance
            return instance
        
        raise ValueError(f"Service {interface.__name__} is not registered")
    
    def resolve_dependencies(self, cls: Type[T]) -> T:
        """Resolve dependencies and create an instance.
        
        Args:
            cls: The class to instantiate with dependency injection
            
        Returns:
            T: The instantiated object with dependencies injected
        """
        # Get the constructor signature
        import inspect
        sig = inspect.signature(cls.__init__)
        
        # Resolve dependencies
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            if param.annotation and param.annotation != inspect.Parameter.empty:
                try:
                    kwargs[param_name] = self.get(param.annotation)
                except ValueError:
                    # If we can't resolve the dependency, skip it
                    # This allows for optional dependencies
                    pass
        
        return cls(**kwargs)


class OFSContainer(DIContainer):
    """OFS-specific dependency injection container.
    
    This container provides pre-configured OFS services and their dependencies.
    """
    
    def __init__(self, config_provider: Optional[ConfigProvider] = None):
        """Initialize the OFS container.
        
        Args:
            config_provider: Optional configuration provider. If None, uses default.
        """
        super().__init__()
        
        # Register configuration provider
        if config_provider is None:
            from .config import OFSConfig
            config_provider = OFSConfig()
        
        self.register_instance(ConfigProvider, config_provider)
        
        # Register default implementations
        self._register_default_implementations()
    
    def _register_default_implementations(self) -> None:
        """Register default implementations for OFS services."""
        # Import implementations
        from .implementations import (
            DefaultIndexManager,
            DefaultPathResolver,
            DefaultDocumentManager,
            DefaultTreeGenerator,
            DefaultKriterienManager
        )
        
        # Register factories that resolve dependencies
        self.register_factory(
            IndexManager,
            lambda: self.resolve_dependencies(DefaultIndexManager)
        )
        
        self.register_factory(
            PathResolver,
            lambda: self.resolve_dependencies(DefaultPathResolver)
        )
        
        self.register_factory(
            DocumentManager,
            lambda: self.resolve_dependencies(DefaultDocumentManager)
        )
        
        self.register_factory(
            TreeGenerator,
            lambda: self.resolve_dependencies(DefaultTreeGenerator)
        )
        
        self.register_factory(
            KriterienManager,
            lambda: self.resolve_dependencies(DefaultKriterienManager)
        )


# Global container instance
_container: Optional[OFSContainer] = None


def get_container() -> OFSContainer:
    """Get the global OFS container instance.
    
    Returns:
        OFSContainer: The global container instance
    """
    global _container
    if _container is None:
        _container = OFSContainer()
    return _container


def set_container(container: OFSContainer) -> None:
    """Set the global OFS container instance.
    
    Args:
        container: The container instance to set as global
    """
    global _container
    _container = container


def reset_container() -> None:
    """Reset the global container instance."""
    global _container
    _container = None