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
- [x] **Document reading functionality** (`read_doc`):
  - `read_doc(identifier, parser)` - Read document content using `Project@Bidder@Filename` format
  - **Intelligent parser selection** with ranking: docling > marker > llamaparse > pdfplumber
  - **Multi-format support**: .txt, .md (plain text), .pdf (with parser selection)
  - **Metadata-aware**: Uses `.pdf2md_index.json` for parser information
  - **Fallback mechanisms**: Graceful handling of missing parsers or content

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
│ ├── cli.py
│ ├── config.py
│ ├── core.py
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
