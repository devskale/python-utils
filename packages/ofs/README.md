# OFS (Opinionated Filesystem)

A Python package for managing opinionated filesystem structures designed to organize tender documents (Ausschreibungsdokumente) and bidder documents (Bieterdokumente) in a standardized, efficient manner.

## Installation

```bash
# Install from source
cd /path/to/ofs
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

## Quick Start

```bash
# Navigate to your OFS directory
cd /path/to/your/.dir

# List all projects
ofs list-projects

# List bidders in a project
ofs list-bidders "ProjectName"

# View project structure
ofs tree

# Analyze criteria for a project
ofs kriterien "ProjectName" pop

# Sync criteria across all projects and bidders
ofs kriterien-sync
```

## Configuration

OFS uses a hierarchical configuration system:

1. **Environment variables** (highest priority)
2. **Local config**: `ofs.config.json` in current directory
3. **User config**: `~/.ofs/config.json`
4. **Defaults** (lowest priority)

### Basic Configuration

```json
{
  "BASE_DIR": ".dir",
  "INDEX_FILE": ".ofs.index.json",
  "METADATA_SUFFIX": ".meta.json"
}
```

### Environment Variables

```bash
export OFS_BASE_DIR="/path/to/documents"
export OFS_INDEX_FILE=".custom.index.json"
```

## CLI Usage

### Core Commands

```bash
# Path resolution
ofs get-path "ProjectName"           # Find project or bidder
ofs root                             # Show OFS root directory

# Project management
ofs list-projects                    # List all projects
ofs list-bidders "ProjectName"       # List bidders in project
ofs find-bidder "Project" "Bidder"   # Find specific bidder

# Document operations
ofs list-docs "ProjectName"          # List project documents
ofs list-docs "Project@Bidder"       # List bidder documents
ofs read-doc "Project@Bidder@doc.pdf" # Read document content

# Structure visualization
ofs tree                             # Show directory tree
ofs tree -d                          # Show directories only
```

### Criteria Management

```bash
# Analyze criteria
ofs kriterien "Project" pop          # Show next unproven criteria
ofs kriterien "Project" tree         # Show criteria hierarchy
ofs kriterien "Project" tag "ID"     # Show specific criterion

# Sync criteria to bidder audits
ofs kriterien-sync                   # Sync all projects/bidders
ofs kriterien-sync "Project"         # Sync all bidders in project
ofs kriterien-sync "Project" "Bidder" # Sync specific bidder

# Record audit events
ofs kriterien-audit ki "Project" "Bidder" "CRITERION_ID"
ofs kriterien-audit mensch "Project" "Bidder" "CRITERION_ID"
ofs kriterien-audit freigabe "Project" "Bidder" "CRITERION_ID"
ofs kriterien-audit ablehnung "Project" "Bidder" "CRITERION_ID"
```

### Index Management

```bash
ofs index create "/path"             # Create index
ofs index update "/path"             # Update existing index
ofs index clear "/path"              # Remove index files
ofs index stats "/path"              # Show index statistics
```

## Python API

```python
import ofs

# Basic operations
path = ofs.get_path("ProjectName")
projects = ofs.list_projects()
bidders = ofs.list_bidders("ProjectName")

# Document management
docs = ofs.list_project_docs_json("ProjectName")
content = ofs.read_doc("Project@Bidder@document.pdf")

# Criteria management
criteria = ofs.load_kriterien("/path/to/kriterien.json")
unproven = ofs.get_unproven_kriterien(criteria)

# Tree structure
tree = ofs.generate_tree_structure()
print(ofs.print_tree_structure())
```

## OFS Structure

OFS organizes documents in a specific directory structure:

```
.dir/                                    # BASE_DIR
├── .ofs.index.json                    # Project index
├── ProjectName/                       # Project folder
│   ├── .ofs.index.json               # Project index
│   ├── A/                            # Tender documents
│   │   ├── document.pdf
│   │   └── md/                       # Processed versions
│   │       └── document.docling.md
│   ├── B/                            # Bidder documents
│   │   ├── BidderName/
│   │   │   ├── bid.pdf
│   │   │   └── md/
│   │   └── audit.json               # Criteria audit
│   ├── projekt.json                 # Project metadata
│   └── kriterien.json               # Evaluation criteria
└── archive/                          # Archived projects
```

### Reserved Directories

- **A/**: Tender documents (Ausschreibungsdokumente)
- **B/**: Bidder documents (Bieterdokumente)
- **md/**: Processed document versions
- **archive/**: Archived content

## Key Concepts

### Document Types

- **Ausschreibungsdokumente**: Tender documents from contracting authorities
- **Bieterdokumente**: Bid documents submitted by bidders
- **Index Files**: `.ofs.index.json` files tracking document metadata
- **Metadata Files**: JSON files with project and document information

### Criteria System

OFS includes a comprehensive criteria evaluation system:

- **kriterien.json**: Defines evaluation criteria for tenders
- **audit.json**: Tracks review status for each bidder's criteria
- **Audit Events**: Record KI reviews, human reviews, approvals, and rejections

### Supported File Types

- PDF (text-based or scanned)
- Office documents (docx, xlsx, pptx)
- Text files (txt)
- Images (jpg, jpeg, png)

## Metadata Files

### projekt.json
Project-level metadata including contracting authority, deadlines, and descriptions.

### kriterien.json
Evaluation criteria with formal requirements, suitability checks, and award criteria.

### audit.json
Per-bidder audit trail tracking criteria review status and events.

### .ofs.index.json
Directory index files tracking document parsing status and available processors.

## Development

### Requirements
- Python >= 3.12

### Project Structure
```
ofs/
├── ofs/                    # Main package
│   ├── cli.py             # Command-line interface
│   ├── core.py            # Main functions
│   ├── config.py          # Configuration system
│   └── [other modules]
├── tests/                 # Test suite
├── setup.py              # Package configuration
└── README.md
```

### Running Tests
```bash
python -m pytest tests/
```

## License

[Add license information here]
