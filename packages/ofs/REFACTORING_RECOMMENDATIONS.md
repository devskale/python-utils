# OFS Refactoring Recommendations

This document provides specific refactoring recommendations aligned with the guidelines outlined in `REFACTOR.md`. The focus is on integrating `pdf2md` indexing functionality into OFS core while maintaining clean architecture and comprehensive functionality.

## Phase 1: Testing and Validation (Immediate Priority)

### 1.1 Test Current pdf2md Indexing Against .dir Structure

**Objective**: Validate that existing `pdf2md` indexing works correctly with OFS `.dir` test directory structure.

**Actions Required**:

```bash
# Test commands to validate current functionality
pdf2md .dir --index --recursive --json
pdf2md .dir --index un --recursive --json
```

**Expected Outcomes**:
- Generate `.ofs.index.json` files in appropriate directories
- Identify unparsed/uncategorized items in `un_items.json`
- Validate parser status tracking (docling, pdfplumber, marker)

**Validation Checklist**:
- [ ] Index files created in project directories (`A/`, `B/BidderName/`)
- [ ] File metadata correctly populated (size, hash, parsers)
- [ ] Parser status accurately reflects processing state
- [ ] Unparsed items correctly identified and listed

### 1.2 Document Current Integration Points

**Create Integration Mapping**:
```python
# Current pdf2md -> OFS mapping
PDF2MD_FUNCTIONS = {
    "index_creation": "pdf2md --index",
    "recursive_indexing": "pdf2md --index --recursive", 
    "unparsed_detection": "pdf2md --index un",
    "json_output": "pdf2md --json"
}

OFS_EQUIVALENTS = {
    "index_creation": "ofs.index.create_index()",
    "recursive_indexing": "ofs.index.update_recursive()",
    "unparsed_detection": "ofs.index.find_unparsed()",
    "json_output": "ofs.core.to_json()"
}
```

## Phase 2: Core Integration (High Priority)

### 2.1 Move Indexing Logic from pdf2md to OFS Core

**Target Architecture**:
```python
# ofs/indexing.py - New centralized indexing module
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

class ParserStatus(Enum):
    """Parser processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class FileIndexEntry:
    """Structured representation of file index entry."""
    name: str
    size: int
    hash: str
    modified: float
    parsers: Dict[str, Any]
    meta: Dict[str, Any]
    
    def is_parsed(self) -> bool:
        """Check if file has been successfully parsed."""
        return self.parsers.get("status") == ParserStatus.COMPLETED.value
    
    def get_available_parsers(self) -> List[str]:
        """Get list of available parsers for this file."""
        return self.parsers.get("det", [])

class OFSIndexManager:
    """Central authority for OFS indexing operations."""
    
    def __init__(self, config: OFSConfig):
        self.config = config
        self.logger = setup_logger(__name__)
    
    def create_index(self, directory: Path, recursive: bool = False) -> OFSResult:
        """Create index files for directory structure."""
        try:
            if recursive:
                return self._create_recursive_index(directory)
            else:
                return self._create_single_index(directory)
        except Exception as e:
            return OFSResult(success=False, error=str(e), error_code="INDEX_CREATION_FAILED")
    
    def update_index(self, directory: Path, recursive: bool = False) -> OFSResult:
        """Update existing index files with new/changed files."""
        # Implementation for updating existing indexes
        pass
    
    def find_unparsed_items(self, directory: Path, recursive: bool = False) -> List[FileIndexEntry]:
        """Find all unparsed or uncategorized items."""
        unparsed_items = []
        
        if recursive:
            for subdir in directory.rglob("*"):
                if subdir.is_dir():
                    unparsed_items.extend(self._scan_directory_for_unparsed(subdir))
        else:
            unparsed_items.extend(self._scan_directory_for_unparsed(directory))
        
        return unparsed_items
    
    def _scan_directory_for_unparsed(self, directory: Path) -> List[FileIndexEntry]:
        """Scan single directory for unparsed items."""
        index_file = directory / self.config.INDEX_FILE
        if not index_file.exists():
            return []
        
        index_data = self._load_index_file(index_file)
        if not index_data:
            return []
        
        unparsed = []
        for file_data in index_data.get("files", []):
            entry = FileIndexEntry(**file_data)
            if not entry.is_parsed() or not entry.meta.get("kategorie"):
                unparsed.append(entry)
        
        return unparsed
```

### 2.2 Implement Backward Compatibility Layer

**Compatibility Interface**:
```python
# ofs/compat.py - Backward compatibility for pdf2md commands
from typing import Optional
import warnings

class PDF2MDCompatibility:
    """Compatibility layer for pdf2md command migration."""
    
    def __init__(self, ofs_manager: OFSIndexManager):
        self.ofs_manager = ofs_manager
    
    def pdf2md_index(self, directory: str, recursive: bool = False, 
                     unparsed_only: bool = False, json_output: bool = False) -> Any:
        """Emulate pdf2md --index command using OFS."""
        warnings.warn(
            "pdf2md indexing is deprecated. Use OFS indexing directly.",
            DeprecationWarning,
            stacklevel=2
        )
        
        dir_path = Path(directory)
        
        if unparsed_only:
            unparsed_items = self.ofs_manager.find_unparsed_items(dir_path, recursive)
            if json_output:
                return self._format_unparsed_json(unparsed_items)
            else:
                return self._format_unparsed_text(unparsed_items)
        else:
            result = self.ofs_manager.create_index(dir_path, recursive)
            if json_output:
                return result.data
            else:
                return f"Index created: {result.success}"
```

### 2.3 Enhanced CLI Integration

**Extended CLI Commands**:
```python
# ofs/cli.py - Enhanced CLI with indexing commands
def add_indexing_commands(parser):
    """Add indexing-related CLI commands."""
    
    # Index creation
    index_parser = parser.add_parser('index', help='Index management commands')
    index_subparsers = index_parser.add_subparsers(dest='index_command')
    
    # Create index
    create_parser = index_subparsers.add_parser('create', help='Create index files')
    create_parser.add_argument('directory', help='Directory to index')
    create_parser.add_argument('--recursive', '-r', action='store_true', 
                              help='Create indexes recursively')
    create_parser.add_argument('--force', '-f', action='store_true',
                              help='Overwrite existing indexes')
    
    # Update index
    update_parser = index_subparsers.add_parser('update', help='Update existing indexes')
    update_parser.add_argument('directory', help='Directory to update')
    update_parser.add_argument('--recursive', '-r', action='store_true')
    
    # Find unparsed
    unparsed_parser = index_subparsers.add_parser('unparsed', help='Find unparsed items')
    unparsed_parser.add_argument('directory', help='Directory to scan')
    unparsed_parser.add_argument('--recursive', '-r', action='store_true')
    unparsed_parser.add_argument('--output', '-o', help='Output file for unparsed items')
    unparsed_parser.add_argument('--json', action='store_true', help='JSON output format')

def handle_index_commands(args, config: OFSConfig):
    """Handle index-related CLI commands."""
    index_manager = OFSIndexManager(config)
    
    if args.index_command == 'create':
        result = index_manager.create_index(Path(args.directory), args.recursive)
        if result.success:
            print(f"Index created successfully in {args.directory}")
        else:
            print(f"Failed to create index: {result.error}")
            return 1
    
    elif args.index_command == 'update':
        result = index_manager.update_index(Path(args.directory), args.recursive)
        if result.success:
            print(f"Index updated successfully in {args.directory}")
        else:
            print(f"Failed to update index: {result.error}")
            return 1
    
    elif args.index_command == 'unparsed':
        unparsed_items = index_manager.find_unparsed_items(Path(args.directory), args.recursive)
        
        if args.json:
            output = json.dumps([item.__dict__ for item in unparsed_items], indent=2)
        else:
            output = f"Found {len(unparsed_items)} unparsed items:\n"
            for item in unparsed_items:
                output += f"  - {item.name} (status: {item.parsers.get('status', 'unknown')})\n"
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Unparsed items saved to {args.output}")
        else:
            print(output)
    
    return 0
```

## Phase 3: Advanced Integration Features

### 3.1 Intelligent Parser Selection

**Smart Parser Assignment**:
```python
class ParserSelector:
    """Intelligent parser selection based on file characteristics."""
    
    PARSER_PREFERENCES = {
        ".pdf": ["docling", "pdfplumber", "marker"],
        ".docx": ["docling"],
        ".xlsx": ["docling"],
        ".txt": ["direct"],
        ".md": ["direct"]
    }
    
    def select_parser(self, file_path: Path, file_size: int) -> List[str]:
        """Select appropriate parsers for file."""
        extension = file_path.suffix.lower()
        base_parsers = self.PARSER_PREFERENCES.get(extension, ["docling"])
        
        # Adjust based on file size
        if file_size > 50 * 1024 * 1024:  # 50MB
            # For large files, prefer memory-efficient parsers
            return [p for p in base_parsers if p != "marker"]
        
        return base_parsers
```

### 3.2 Categorization Integration

**Automated Categorization**:
```python
class DocumentCategorizer:
    """Automated document categorization for OFS."""
    
    CATEGORY_PATTERNS = {
        "Eignungsnachweise": ["eignung", "qualification", "suitability"],
        "Berufliche Zuverlässigkeit": ["zuverlässigkeit", "reliability", "criminal"],
        "Angebot": ["angebot", "offer", "bid", "proposal"],
        "Preisblatt": ["preis", "price", "cost", "pricing"]
    }
    
    def categorize_document(self, file_name: str, content_preview: str = "") -> Optional[str]:
        """Automatically categorize document based on name and content."""
        text_to_analyze = f"{file_name} {content_preview}".lower()
        
        for category, patterns in self.CATEGORY_PATTERNS.items():
            if any(pattern in text_to_analyze for pattern in patterns):
                return category
        
        return None
```

### 3.3 Migration Utilities

**Data Migration Tools**:
```python
class OFSMigrationTool:
    """Tools for migrating from pdf2md to OFS indexing."""
    
    def migrate_pdf2md_indexes(self, base_directory: Path) -> OFSResult:
        """Migrate existing pdf2md indexes to OFS format."""
        migration_log = []
        
        for old_index in base_directory.rglob("ofs.index.json"):
            try:
                new_index_path = old_index.parent / ".ofs.index.json"
                
                # Load old format
                with open(old_index, 'r') as f:
                    old_data = json.load(f)
                
                # Convert to new format
                new_data = self._convert_index_format(old_data)
                
                # Save new format
                with open(new_index_path, 'w') as f:
                    json.dump(new_data, f, indent=2)
                
                migration_log.append(f"Migrated: {old_index} -> {new_index_path}")
                
            except Exception as e:
                migration_log.append(f"Failed to migrate {old_index}: {e}")
        
        return OFSResult(success=True, data=migration_log)
    
    def _convert_index_format(self, old_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert old index format to new OFS format."""
        # Implementation for format conversion
        pass
```

## Implementation Timeline

### Week 1-2: Foundation
- [ ] Implement `OFSIndexManager` core class
- [ ] Create `FileIndexEntry` data structures
- [ ] Add basic index creation/update functionality
- [ ] Write comprehensive unit tests

### Week 3-4: Integration
- [ ] Integrate indexing with existing OFS CLI
- [ ] Implement backward compatibility layer
- [ ] Add parser selection logic
- [ ] Test against existing `.dir` structure

### Week 5-6: Advanced Features
- [ ] Implement automated categorization
- [ ] Add migration utilities
- [ ] Performance optimization
- [ ] Documentation updates

### Week 7-8: Testing and Deployment
- [ ] Comprehensive integration testing
- [ ] Performance benchmarking
- [ ] Migration testing with real data
- [ ] Final documentation and examples

## Success Criteria

1. **Functional Parity**: All `pdf2md` indexing functionality available through OFS
2. **Performance**: Index operations complete within 10% of original `pdf2md` performance
3. **Compatibility**: Existing workflows continue to function with deprecation warnings
4. **Reliability**: 99%+ success rate for index operations on valid directory structures
5. **Maintainability**: Clear separation of concerns with comprehensive test coverage

## Risk Mitigation

### Data Loss Prevention
- Always backup existing index files before migration
- Implement atomic operations for index updates
- Validate index integrity after operations

### Performance Concerns
- Implement caching for frequently accessed indexes
- Use lazy loading for large directory structures
- Provide progress indicators for long-running operations

### Compatibility Issues
- Maintain parallel operation during transition period
- Provide clear migration path documentation
- Implement feature flags for gradual rollout

## Conclusion

This refactoring plan aligns with the `REFACTOR.md` vision of making OFS the central indexing authority while maintaining backward compatibility and improving overall system architecture. The phased approach ensures minimal disruption to existing workflows while providing a clear path to enhanced functionality.