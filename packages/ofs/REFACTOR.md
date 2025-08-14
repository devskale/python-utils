# OFS Refactoring Plan - Simplified Indexing Integration

## Overview

This simplified refactoring plan focuses on two core objectives:
1. Test the existing pdf2md indexing system against the `.dir` test directory
2. Integrate the indexing functionality into OFS core and import it from there for pdf2md usage

## Current State

### Existing Components
- **pdf2md.skale**: Uses `.pdf2md_index.json` for parsing status tracking
- **ofs**: Basic path resolution and project discovery
- **Test Environment**: `.dir` symbolic link to `C:\Users\Hans\Documents\klark0\.dir` pointing to packages directory

### Integration Goal
Move indexing logic from pdf2md into OFS core, making OFS the central indexing authority that pdf2md imports and uses.

## Phase 1: Test Current Indexing Against .dir

### 1.1 Validate Current pdf2md Indexing

**Objective**: Ensure pdf2md indexing works correctly with the `.dir` test environment

**Tasks**:
1. Run pdf2md indexing against `.dir` structure
2. Verify `.pdf2md_index.json` creation and updates
3. Test parsing workflow with existing indexing
4. Document any issues or limitations

**Test Commands**:

```bash
usage: pdf2md [-h] [--version] [--overwrite] [--ocr] [--ocr-lang OCR_LANG] [--parsers PARSERS [PARSERS ...]] [--recursive] [--dry] [--update] [--clear-parser CLEAR_PARSER] [--index {create,update,clear,test,stats,un}] [-J]
              [-o OUTPUT] [--index-age INDEX_AGE] [--status [STATUS]] [--unfile NUM]
              [input_path]

Convert PDF to Markdown Installation: pip install git+https://github.com/devskale/python-utils.git#subdirectory=packages/pdf2md.skale

positional arguments:
  input_path            Path to PDF file or directory containing PDF files (default: )

options:
  -h, --help            show this help message and exit
  --version             Show version and exit
  --overwrite           Overwrite existing files
  --ocr                 Use OCR for text extraction
  --ocr-lang OCR_LANG   Language for OCR (default: deu)
  --parsers PARSERS [PARSERS ...]
                        List of parsers to use (available: pdfplumber, pypdf2, pymupdf, llamaparse, docling, marker; default: pdfplumber)
  --recursive           Process directories recursively
  --dry                 Dry run - show file counts without conversion
  --update              Update pdf2md to the latest version from GitHub
  --clear-parser CLEAR_PARSER
                        Clear markdown files for a specific parser (e.g. 'marker')
  --index {create,update,clear,test,stats,un}
                        Index operations: create new index, update existing, clear all indexes, test index update (dry run), print stats, or list unparsed and uncategorized items
  -J, --json            Output the result in JSON format (used with --index un)
  -o OUTPUT, --output OUTPUT
                        Specify the output file (used with --index un)
  --index-age INDEX_AGE
                        Maximum age (in seconds) for index files before they're considered stale (default: 30)
  --status [STATUS]     Show parsing status. Provide a parser name to see files not yet parsed by it. Without a name, it shows completely unparsed files.
  --unfile NUM          Process NUM unparsed files from un_items.json file. Requires input_path to be the JSON file or directory containing it.
```

```bash
# A link to the testdir is present in each package sourcedirectory accessible via .dir


# Test pdf2md indexing
pdf2md .dir --index --recursive
python -m pdf2md parse --queue

# Verify index files
find . -name ".pdf2md_index.json" -exec cat {} \;
```



**Success Criteria**:
- Index files are created in appropriate directories
- PDF files are correctly identified and tracked
- Parsing status is accurately maintained
- No errors during indexing or parsing operations

## Phase 2: Move Indexing to OFS Core

### 2.1 Extract Indexing Logic from pdf2md

**Objective**: Move indexing functionality from pdf2md to OFS

**Implementation**:

1. **Create OFS Indexing Module**:
```python
# ofs/indexing.py
class OFSIndexManager:
    def __init__(self, directory_path: str):
        self.directory_path = Path(directory_path)
        self.index_file = self.directory_path / ".ofs_index.json"
    
    def create_index(self) -> Dict[str, Any]:
        """Create or update index for directory"""
        pass
    
    def get_pdf_files(self) -> List[str]:
        """Get list of PDF files in directory"""
        pass
    
    def update_file_status(self, filename: str, status: str):
        """Update processing status for a file"""
        pass
    
    def get_unparsed_files(self) -> List[str]:
        """Get list of files that need parsing"""
        pass
```

2. **Migrate Index Schema**:
```json
{
  "schema_version": "1.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "directory": "/path/to/directory",
  "files": [
    {
      "name": "document.pdf",
      "size": 1024000,
      "last_modified": "2024-01-15T09:00:00Z",
      "parsing_status": "unparsed|parsed|failed",
      "parsed_file": "document.md",
      "parser_used": "marker",
      "parse_timestamp": "2024-01-15T09:15:00Z"
    }
  ]
}
```

### 2.2 Update pdf2md to Use OFS Indexing

**Objective**: Modify pdf2md to import and use OFS indexing instead of its own

**Changes Required**:

1. **Update pdf2md imports**:
```python
# In pdf2md modules
from ofs.indexing import OFSIndexManager

# Replace existing indexing calls
index_manager = OFSIndexManager(directory_path)
files_to_parse = index_manager.get_unparsed_files()
```

2. **Remove pdf2md indexing code**:
- Remove `.pdf2md_index.json` creation logic
- Remove internal file tracking
- Update CLI commands to use OFS indexing

3. **Update dependencies**:
```python
# pdf2md setup.py
install_requires=[
    "ofs>=2.0.0",  # Add OFS dependency
    # ... other dependencies
]
```

## Implementation Steps

### Step 1: Test Current System
```bash
# 1. Test pdf2md with .dir
cd .dir
python -m pdf2md index --recursive
python -m pdf2md status

# 2. Document current behavior
# - Note index file locations
# - Record file counts and status
# - Test parsing workflow
```

### Step 2: Create OFS Indexing
```bash
# 1. Create indexing module in OFS
touch ofs/indexing.py

# 2. Implement OFSIndexManager class
# 3. Add tests for indexing functionality
# 4. Update OFS setup.py to expose indexing
```

### Step 3: Migrate pdf2md
```bash
# 1. Update pdf2md to import from OFS
# 2. Remove redundant indexing code
# 3. Test integration
# 4. Update documentation
```

### Step 4: Validation
```bash
# 1. Test complete workflow with .dir
# 2. Verify backward compatibility
# 3. Performance testing
# 4. Documentation updates
```

## File Structure After Refactoring

```
packages/
├── ofs/
│   ├── ofs/
│   │   ├── __init__.py
│   │   ├── core.py
│   │   ├── indexing.py          # New: Centralized indexing
│   │   ├── cli.py
│   │   └── ...
│   └── setup.py
├── pdf2md.skale/
│   ├── pdf2md/
│   │   ├── __init__.py
│   │   ├── main.py              # Modified: Uses OFS indexing
│   │   ├── converter.py
│   │   └── ...
│   └── setup.py                 # Modified: Adds OFS dependency
└── .dir -> C:\Users\Hans\Documents\klark0\.dir
```

## Success Criteria

### Phase 1 Success
- [ ] pdf2md indexing works correctly with `.dir`
- [ ] All PDF files are discovered and tracked
- [ ] Index files are created in correct locations
- [ ] Parsing workflow completes without errors

### Phase 2 Success
- [ ] OFS indexing module is functional
- [ ] pdf2md successfully imports and uses OFS indexing
- [ ] No regression in pdf2md functionality
- [ ] Index format is compatible or properly migrated
- [ ] All tests pass

## Timeline

**Week 1**: Phase 1 - Test current indexing with `.dir`
- Day 1-2: Set up test environment and run indexing tests
- Day 3-4: Document current behavior and identify issues
- Day 5: Validate parsing workflow

**Week 2**: Phase 2 - Implement OFS indexing integration
- Day 1-2: Create OFS indexing module
- Day 3-4: Migrate pdf2md to use OFS indexing
- Day 5: Testing and validation

## Risk Mitigation

1. **Backup Strategy**: Keep original pdf2md indexing code until migration is validated
2. **Incremental Testing**: Test each component separately before integration
3. **Rollback Plan**: Maintain ability to revert to original indexing if issues arise
4. **Documentation**: Document all changes and migration steps

## Next Steps After Completion

Once this simplified refactoring is complete and validated:
1. Consider expanding OFS indexing to support strukt2meta
2. Add workflow orchestration capabilities
3. Implement background processing
4. Add AI agentic APIs

This simplified approach focuses on the core integration without the complexity of the full workflow orchestration system, making it more manageable and less risky to implement.