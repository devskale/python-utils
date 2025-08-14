# OFS Dependency Injection Implementation

This document describes the dependency injection architecture implemented in the OFS (Opinionated Filesystem) package.

## Overview

The dependency injection implementation provides a clean, testable, and maintainable architecture while preserving full backward compatibility with existing code. The implementation follows the architectural improvements outlined in `IMPROVEMENTS.md`.

## Architecture Components

### 1. Interfaces (`interfaces.py`)

Defines abstract protocols for all major OFS components:

- **`ConfigProvider`**: Configuration management interface
- **`IndexManager`**: Search index operations interface
- **`PathResolver`**: Path resolution and navigation interface
- **`DocumentManager`**: Document access and management interface
- **`TreeGenerator`**: Directory tree generation interface
- **`KriterienManager`**: Criteria analysis interface

```python
from ofs import ConfigProvider, IndexManager, PathResolver

# All interfaces use Protocol for type safety
class MyCustomConfig(ConfigProvider):
    def get(self, key: str, default: Any = None) -> Any:
        # Custom implementation
        pass
```

### 2. Dependency Injection Container (`container.py`)

Provides service registration and resolution:

- **`DIContainer`**: Generic dependency injection container
- **`OFSContainer`**: OFS-specific container with default registrations
- **Global container management**: `get_container()`, `set_container()`, `reset_container()`

```python
from ofs import get_container, ConfigProvider

# Get services from container
container = get_container()
config = container.get(ConfigProvider)
```

### 3. Default Implementations (`implementations.py`)

Concrete implementations that wrap existing OFS functionality:

- **`DefaultIndexManager`**: Wraps existing index operations
- **`DefaultPathResolver`**: Wraps existing path operations
- **`DefaultDocumentManager`**: Wraps existing document operations
- **`DefaultTreeGenerator`**: Wraps existing tree operations
- **`DefaultKriterienManager`**: Wraps existing criteria operations

### 4. Service Layer (`services.py`)

High-level service that coordinates between components:

- **`OFSService`**: Main service class with dependency injection
- **Global service management**: `get_ofs_service()`, `set_ofs_service()`, `reset_ofs_service()`

```python
from ofs import get_ofs_service

# Use high-level service
service = get_ofs_service()
projects = service.list_projects()
bidders = service.list_bidders("MyProject")
```

## Usage Patterns

### 1. Legacy Usage (Backward Compatible)

```python
# All existing code continues to work unchanged
from ofs import get_config, list_projects, list_bidders

config = get_config()
projects = list_projects()
bidders = list_bidders("MyProject")
```

### 2. Service Layer Usage

```python
# Use the new service layer for cleaner API
from ofs import get_ofs_service

service = get_ofs_service()
projects = service.list_projects()
bidders = service.list_bidders("MyProject")
path = service.get_path("MyProject")
tree = service.generate_tree(directories_only=True)
```

### 3. Direct Dependency Injection

```python
# Use dependency injection directly
from ofs import get_container, ConfigProvider, PathResolver

container = get_container()
config = container.get(ConfigProvider)
path_resolver = container.get(PathResolver)

projects = path_resolver.list_projects()
```

### 4. Custom Implementations

```python
# Create custom implementations
from ofs import (
    DIContainer, ConfigProvider, PathResolver,
    set_container, DefaultPathResolver
)

class CustomConfig(ConfigProvider):
    def get(self, key: str, default=None):
        # Custom configuration logic
        return custom_value

# Create custom container
custom_container = DIContainer()
custom_config = CustomConfig()
custom_container.register_instance(ConfigProvider, custom_config)

# Register path resolver with custom config
path_resolver = DefaultPathResolver(custom_config)
custom_container.register_instance(PathResolver, path_resolver)

# Set as global container
set_container(custom_container)
```

## Testing

The implementation includes comprehensive tests:

### 1. Dependency Injection Tests

```bash
python test_dependency_injection.py
```

Tests:
- Backward compatibility
- Container functionality
- Service layer operations
- Default implementations
- Custom container configuration
- Error handling

### 2. Original Command Tests

```bash
python test_ofs_commands.py
```

Ensures all existing CLI commands continue to work correctly.

## Benefits

### 1. **Testability**
- Easy to mock dependencies for unit testing
- Isolated component testing
- Dependency injection enables test doubles

### 2. **Maintainability**
- Clear separation of concerns
- Explicit dependencies
- Easier to understand component relationships

### 3. **Flexibility**
- Easy to swap implementations
- Support for different configurations
- Extensible architecture

### 4. **Backward Compatibility**
- All existing code continues to work
- Gradual migration path
- No breaking changes

## Migration Guide

### Phase 1: Use Service Layer

Replace direct function calls with service layer:

```python
# Before
from ofs import list_projects, list_bidders
projects = list_projects()

# After
from ofs import get_ofs_service
service = get_ofs_service()
projects = service.list_projects()
```

### Phase 2: Use Dependency Injection

For new code, use dependency injection:

```python
class MyAnalyzer:
    def __init__(self, path_resolver: PathResolver, document_manager: DocumentManager):
        self.path_resolver = path_resolver
        self.document_manager = document_manager
    
    def analyze_project(self, project_name: str):
        path = self.path_resolver.get_path(project_name)
        docs = self.document_manager.list_documents(project_name)
        # Analysis logic

# Usage
container = get_container()
analyzer = MyAnalyzer(
    container.get(PathResolver),
    container.get(DocumentManager)
)
```

### Phase 3: Custom Implementations

Create custom implementations for specific needs:

```python
class DatabaseConfig(ConfigProvider):
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get(self, key: str, default=None):
        # Load from database
        return self.db.get_config(key, default)
```

## Configuration

The dependency injection system uses the existing `OFSConfig` class as the default `ConfigProvider`. Custom configurations can be injected:

```python
from ofs import set_container, DIContainer, ConfigProvider
from ofs.config import OFSConfig

# Create custom configuration
class TestConfig(OFSConfig):
    def __init__(self):
        super().__init__()
        # Override specific settings for testing
        self._config['BASE_DIR'] = '/test/data'

# Use in tests
test_container = DIContainer()
test_container.register_instance(ConfigProvider, TestConfig())
set_container(test_container)
```

## Error Handling

The dependency injection system includes robust error handling:

- **Missing dependencies**: Clear error messages when services aren't registered
- **Circular dependencies**: Detection and prevention
- **Graceful fallbacks**: Default implementations when custom ones fail
- **Type safety**: Protocol-based interfaces ensure type compatibility

## Performance Considerations

- **Singleton pattern**: Services are created once and reused
- **Lazy initialization**: Services created only when needed
- **Minimal overhead**: Dependency resolution is fast
- **Memory efficient**: Shared instances reduce memory usage

## Future Enhancements

The architecture supports future improvements:

1. **Async support**: Easy to add async versions of interfaces
2. **Plugin system**: Dynamic service registration
3. **Configuration validation**: Type-safe configuration schemas
4. **Monitoring**: Service usage tracking and metrics
5. **Caching**: Intelligent caching strategies

## Conclusion

The dependency injection implementation provides a solid foundation for the OFS package's future development while maintaining complete backward compatibility. It enables better testing, cleaner architecture, and easier maintenance without disrupting existing workflows.