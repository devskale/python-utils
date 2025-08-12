# OFS Core / Shared Index Service PRD (Consolidated)

1. Overview

---

Create a python library to access, edit and navigate the opinionated filesystem (OFS), described in docs/opinionatedFilesystem.md

# TODO

✅ get_path('name') -> str - IMPLEMENTED (uses BASE_DIR from config)

## Implementation Status

### Completed ✅
- [x] Basic package structure (`ofs/`)
- [x] Core module (`ofs/core.py`) with enhanced `get_path` function
- [x] CLI interface (`ofs/cli.py`) with comprehensive command set
- [x] Package configuration (`setup.py`) for Python 3.12+ and setuptools
- [x] Configuration system (`ofs/config.py`) with environment variables, config files, and defaults
- [x] Comprehensive test suite (`tests/`) covering all functionality
- [x] Updated `README.md` with complete documentation
- [x] Default configuration file (`ofs.config.json`) with `BASE_DIR: ".dir"`
- [x] **Enhanced `get_path` function** with intelligent search algorithm:
  - Direct filesystem matching
  - `.pdf2md_index.json` file parsing and searching
  - Recursive directory traversal
  - AUSSCHREIBUNGNAME and BIETERNAME resolution
- [x] **Project and bidder management functions**:
  - `list_projects()` - List all AUSSCHREIBUNGNAME
  - `list_bidders(project)` - List BIETERNAME in a project
  - `find_bidder_in_project(project, bidder)` - Locate specific bidder
- [x] **Extended CLI commands**:
  - `ofs get-path <name>` - Find projects or bidders
  - `ofs list-projects` - List all projects
  - `ofs list-bidders <project>` - List bidders in project
  - `ofs find-bidder <project> <bidder>` - Find specific bidder
  - `ofs list-docs <project@bidder>` - List bidder documents with minimal view (name + basic metadata)
  - `ofs list-docs <project@bidder> --meta` - List bidder documents with full metadata and details
  - `ofs list-docs <project>` - List project documents from A/ folder with minimal view (name + basic metadata)
  - `ofs list-docs <project> --meta` - List project documents from A/ folder with full metadata and details
  - `ofs list-docs <project@bidder@filename>` - Get detailed information for a specific document
  - `ofs tree` - Show tree structure of projects, bidders, and documents
  - `ofs tree -d` - Show only directory tree (no documents)
- [x] **Module execution support** (`ofs/__main__.py`)
- [x] **Tree structure visualization**:
  - `generate_tree_structure()` - Generate structured tree data
  - `print_tree_structure()` - Format tree for display
  - Support for directories-only mode
  - **Reserved directory filtering** - Excludes 'md/' and 'archive/' directories from tree output
  - **Reserved file filtering** - Excludes '.json' and '.md' files from tree output
### `read_doc(doc_id, parser=None)`

This function is the core of the document reading capability. It intelligently selects the appropriate parser based on the document type and available parsers, and extracts content from pre-parsed Markdown files located in `md/` subfolders.

**Features:**
- **Intelligent Parser Selection:** Uses `_select_parser` to choose the best parser based on the `.pdf2md_index.json` metadata.
- **Pre-parsed Markdown Reading:** Prioritizes reading from `md/` subfolders, supporting various naming conventions (e.g., `filename.parser.md`, `filename_parser.md`, and `md/<base_name>/` subfolders).
- **Multi-format Support:** Handles `.txt`, `.md` (pre-parsed), and `.pdf` (original, for fallback/initial processing if no pre-parsed markdown is found) extensions.
- **Fallback Mechanism:** If a specified parser's Markdown file is not found, it attempts to find other available Markdown versions or falls back to original PDF processing if necessary.
- **Metadata Inclusion:** Returns extracted content along with parser details and original file path.

**Usage:**
```python
# Read a document, letting the system select the best parser (will read from pre-parsed Markdown)
content = ofs.read_doc('Aufsitzrasenmäher@Bieter1@LSD-BG.pdf')

# Read a document, forcing a specific parser (will read the corresponding pre-parsed Markdown)
content = ofs.read_doc('Aufsitzrasenmäher@Bieter1@LSD-BG.pdf', parser='pdfplumber')

# Read a tender document (example for tender-specific parsing)
content = ofs.read_doc('2023_02002_AAB_EV.pdf', parser='docling')
```

### In Progress 🚧
- [ ] Performance optimization for large directory structures
- [ ] Caching mechanism for index file parsing

### Planned 📋
- [ ] Metadata sidecar file handling and editing
- [ ] Index file management and updates
- [ ] File editing capabilities with metadata preservation
- [ ] Rich filesystem navigation with breadcrumbs
- [ ] Documentation generation from metadata
- [ ] Integration with external tools (pdf2md, etc.)

# Project structure

markdown ```
.
├── ofs/
│ ├── __init__.py
│ ├── __main__.py
│ ├── cli.py
│ ├── config.py
│ ├── core.py        # Aggregator module for backward compatibility
│ ├── paths.py       # Path resolution and OFS navigation
│ ├── docs.py        # Document listing and reading functionality
│ ├── tree.py        # Directory tree structure generation
├── tests/
├── docs/
│ ├── opinionatedFilesystem.md
│ ├── tree.dir
├── .dir
├── .trae/
│ ├── rules/
│ │ ├── project_rules.md
├── setup.py
├── PRD.md
```

# Code Architecture

## Module Decomposition (December 2024)

The OFS package has been decomposed from a single large `core.py` file (~1,500 lines) into smaller, maintainable modules:

### `ofs/paths.py` - Path Resolution
- Path finding and navigation functions
- OFS structure traversal
- Project and bidder discovery
- Index file parsing utilities
- Functions: `get_path`, `find_bidder_in_project`, `list_projects`, `list_bidders`, etc.

### `ofs/docs.py` - Document Management
- Document listing and metadata handling
- Document reading with parser selection
- Content extraction for various file formats
- Functions: `read_doc`, `list_bidder_docs_json`, `list_project_docs_json`, etc.

### `ofs/tree.py` - Tree Structure
- Directory tree generation and formatting
- Visual structure representation
- Functions: `generate_tree_structure`, `print_tree_structure`

### `ofs/core.py` - Backward Compatibility Aggregator
- Imports and re-exports all functions from decomposed modules
- Maintains full backward compatibility for existing code
- No breaking changes to existing APIs

### Benefits of Decomposition
- **Maintainability**: Smaller, focused modules (300-500 lines each)
- **Testability**: Easier to unit test individual components
- **Code Organization**: Clear separation of concerns
- **Development**: Faster development with focused modules
- **Backward Compatibility**: Zero breaking changes for existing users
