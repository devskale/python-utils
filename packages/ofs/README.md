# OFS (Opinionated Filesystem)

A Python package for accessing, editing, and navigating opinionated filesystem structures designed to organize tender documents (Ausschreibungsdokumente) and bidder documents (Bieterdokumente) in a standardized, efficient manner. This structure facilitates AI-assisted legal analysis, ensuring modularity, easy navigation, and integration with processing tools.

- **Ausschreibungsdokumente**: Documents created and published by the contracting authority to inform potential bidders about the tender. They include performance descriptions, participation conditions, contract terms, and deadlines.
- **Bieterdokumente**: Documents submitted by bidders, including offers, price sheets, suitability proofs, and possibly concepts or technical solutions.

The structure supports local and remote storage (e.g., via WebDAV) and is optimized for processing pipelines like PDF to Markdown conversion.

## Supported File Types

The system supports the following file types for documents:

- PDF (text-based or scanned)
- Office documents (docx, xlsx, pptx)
- Text files (txt)
- Images (jpg, jpeg, png)

Processed outputs include Markdown (.md) and JSON metadata.

## Installation

### Development Installation

1. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
```

2. Install in development mode:

```bash
pip install -e .
```

## Usage

### Command Line Interface

```bash
# Get path for a project (AUSSCHREIBUNGNAME) or bidder (BIETERNAME)
ofs get-path "Demoprojekt1"
ofs get-path "Demo2"

# List all available items (projects, bidders, files)
ofs list

# List all projects (AUSSCHREIBUNGNAME)
ofs list-projects

# List all bidders in a specific project
ofs list-bidders "Demoprojekt1"

# Find a specific bidder within a project
ofs find-bidder "Demoprojekt1" "Demo2"

# Get OFS root directory
ofs root

# Get paths in JSON format
ofs get-paths-json "Demoprojekt1"

# List projects in JSON format
ofs list-projects-json

# Index management commands
ofs index create .dir --recursive    # Create index files
ofs index update .dir --recursive    # Update existing index files
ofs index clear .dir --recursive     # Clear/remove index files
```

### Python API

```python
import ofs

# Get path for a project or bidder
project_path = ofs.get_path("Demoprojekt1")
print(project_path)  # Output: .dir/Demoprojekt1

bidder_path = ofs.get_path("Demo2")
print(bidder_path)  # Output: .dir/Demoprojekt1/B/Demo2

# List all items (includes projects, bidders, files from filesystem and index files)
items = ofs.list_ofs_items()
print(items)

# List all projects
projects = ofs.list_projects()
print(projects)  # Output: ['2025-04 Lampen', 'Demoprojekt1', ...]

# List bidders in a project
bidders = ofs.list_bidders("Demoprojekt1")
print(bidders)  # Output: ['Demo2', 'Demo4', 'Siemens AG', ...]

# Find specific bidder in project
bidder_path = ofs.find_bidder_in_project("Demoprojekt1", "Demo2")
print(bidder_path)  # Output: .dir/Demoprojekt1/B/Demo2

# Get OFS root
root = ofs.get_ofs_root()
print(root)

# Access paths in JSON format
paths_json = ofs.get_paths_json("Demoprojekt1")
print(paths_json)

# List projects in JSON format
projects_json = ofs.list_projects_json()
print(projects_json)

# Access configuration
config = ofs.get_config()
base_dir = config.get("BASE_DIR")
print(base_dir)  # Output: .dir
```

## OFS Structure

OFS is designed to handle tender documentation with a specific directory structure:

### Top-Level Structure

The root directory (e.g., `.dir/`) contains active tender project folders and an archive:

- **Project Folder** (named after the tender, e.g., `2025-04 Lampen` or `A-TEST`):
  - **A/**: Directory for tender documents (Ausschreibungsdokumente)
    - Contains original files (PDFs, DOCX, etc.)
    - **md/**: Subdirectory for Markdown conversions of tender documents
      - Includes converted .md files and subdirectories for extracted content (e.g., images from PDFs)
  - **B/**: Directory for bidder documents (Bieterdokumente)
    - **BIETERNAME/** (e.g., `Lampion`): Subdirectory for each bidder's documents
      - Original bidder files
      - **md/**: Markdown conversions of bidder documents
      - **archive/**: Holds archived versions of bidder directories
  - **projekt.meta.json**: Project metadata file
  - **kriterien.meta.json** (optional): Criteria metadata
- **archive/**: Directory for archived projects
  - Contains moved project folders (e.g., archived `Ausschreibungsname`)

### Reserved Directory Names

These directories have specific purposes and should not be used for other content:

- **A**: Exclusively for tender project documents
- **B**: Exclusively for bidder documents
- **md**: Contains Markdown-converted versions of documents and extracted assets (e.g., images from PDFs)
- **proc**: (Future) For other processed document versions (e.g., anonymized or analyzed outputs)
- **archive**: For archiving projects or sub-elements (e.g., old bidder submissions)

### Example Structure

```
.dir/                                    # BASE_DIR (configurable)
├── .ofs.index.json                    # Index file with project listings
├── 2025-04 Lampen/                     # Project folder
│   ├── .ofs.index.json               # Project-level index
│   ├── A/                             # Tender documents
│   │   ├── 2024_06001_AAB_EV.pdf      # Original tender document
│   │   ├── 2024_06001_Beilage_01.docx # Original attachment
│   │   ├── .ofs.index.json          # Directory index
│   │   └── md/                        # Markdown conversions
│   │       ├── 2024_06001_AAB_EV.docling.md       # Converted via docling
│   │       ├── 2024_06001_AAB_EV.pdfplumber.md    # Converted via pdfplumber
│   │       └── 2024_06001_AAB_EV/                 # Extracted assets
│   │           ├── _page_0_Picture_5.jpeg         # Extracted image
│   │           └── 2024_06001_AAB_EV.marker.md    # Marker conversion
│   ├── B/                             # Bidder documents
│   │   ├── .ofs.index.json          # Bidder directory index
│   │   ├── Lampion/                   # Specific bidder folder
│   │   │   ├── 1completed-austrian-document.pdf   # Original bidder document
│   │   │   └── md/                    # Markdown conversions
│   │   │       ├── 1completed-austrian-document.docling.md
│   │   │       └── 1completed-austrian-document/
│   │   │           └── 1completed-austrian-document.marker.md
│   │   └── archive/                   # Archived bidder folders
│   │       └── Lampion2/              # Archived version of bidder
│   ├── projekt.meta.json              # Project metadata
│   └── kriterien.meta.json            # Extracted criteria
├── A-TEST/                            # Another project
│   ├── A/
│   ├── B/
│   └── projekt.meta.json
└── archive/                           # Archived projects
    └── OldProject/                    # Archived project folder
```

This structure ensures separation between tender and bidder data, with processed versions isolated in `md/` subdirectories.

### Search Algorithm

The `get_path` function uses an intelligent search algorithm:

1. **Direct filesystem match**: Searches for exact directory/file names
2. **Index file search**: Looks in `.ofs.index.json` files for entries
3. **Recursive search**: Traverses subdirectories to find nested items
4. **Bidder-specific search**: Automatically searches in `B/` subdirectories for bidder names

This allows you to find both projects (`AUSSCHREIBUNGNAME`) and bidders (`BIETERNAME`) regardless of their exact location in the filesystem.

## Recent Updates

### Index File System Improvements

**Version Update**: The OFS index file naming system has been updated to use hidden files for better user experience.

**Changes Made**:
- Index files are now named `.ofs.index.json` (hidden files) instead of `ofs.index.json`
- Updated configuration default for `INDEX_FILE` to `.ofs.index.json`
- All existing functionality remains unchanged
- Cleaner directory appearance for end users (index files are hidden from normal listings)

**Migration**: The system automatically handles the transition from old to new index file names. Use the following commands to migrate:

```bash
# Clear old index files and create new ones
python -m ofs index clear .dir --recursive
python -m ofs index create .dir --recursive
```

**Benefits**:
- Hidden index files provide cleaner directory listings
- Maintains all existing OFS functionality
- Index files are still accessible through OFS commands
- Better user experience when browsing directories

## Metadata Files and Reserved Filenames

OFS uses several types of metadata files to track document processing, project information, and criteria extraction. These files enable efficient data retrieval, integrity checks, and integration with AI analysis tools.

### Reserved Filenames

Certain filenames are reserved for system-generated content:

- **md/filename_PROCESSOR.md**: Markdown-converted version of the source document. `_PROCESSOR` indicates the converter used (e.g., `docling`, `pdfplumber`, `marker` for scanned PDFs)
- **md/filename/**: A subdirectory for extracted contents from the source file, such as images (`_page_X_Picture_Y.jpeg`) or additional .md files
- **PROJEKTNAME.md** (e.g., in project root): Contains automatically extracted information about the project, such as summaries or key details from documents

### Core Metadata Files

#### 1. projekt.meta.json (Project-Level Metadata)

**Location**: Project root (e.g., `2025-04 Lampen/projekt.meta.json`)

**Purpose**: Stores comprehensive metadata about the project and its documents. Used for UI, search, and enrichment context.

**Example Structure**:
```json
{
  "vergabestelle": "Wiener Wohnen Hausbetreuung GmbH",
  "adresse": "Erdbergstraße 200, 1030 Wien",
  "projektName": "Leuchten, Masten, Ausleger",
  "startDatum": "NONE",
  "bieterabgabe": "2025-06-16",
  "projektStart": "NONE",
  "endDatum": "NONE",
  "beschreibung": "Öffentliches Vergabeverfahren über die Lieferung von Leuchten, Lichtmasten und Auslegern an den Auftraggeber.",
  "referenznummer": "AS 2024.06001",
  "schlagworte": "Ausschreibung, Vergabeverfahren, Offenes Verfahren, Oberschwellenbereich, BVergG 2018, Rahmenvertrag, Lieferauftrag, Leuchten, Lichtmasten, Ausleger",
  "sprache": "Deutsch",
  "dokumentdatum": "2025-07-31",
  "selectedParser": null,
  "metadaten": []
}
```

**Key Fields**:
- `projektName`: Human readable project name
- `referenznummer`: Tender reference / internal ID
- `vergabestelle`: Contracting authority
- `bieterabgabe`: Bid submission deadline
- `beschreibung`: Short summary (<= 600 chars)
- `schlagworte`: Comma-separated keywords

#### 2. kriterien.meta.json (Extracted Criteria)

**Location**: Project root (optional; created when criteria extraction runs successfully)

**Purpose**: Central structured representation of award & suitability criteria for scoring, compliance checking, and bid guidance.

**Example Structure**:
```json
{
  "extractedCriteria": {
    "eignungskriterien": { },
    "zuschlagskriterien": [ ],
    "subunternehmerregelung": [ ],
    "formale_anforderungen": [ ]
  },
  "extractionTimestamp": "2025-07-31T14:09:10.449Z",
  "extractionMethod": "KRITERIEN_EXTRAKTION",
  "aabFileName": "2023_02002_AAB_EV.pdf",
  "lastModified": "2025-07-31T14:09:10.449Z",
  "version": "1.0",
  "reviewStatus": {
    "aiReviewed": true,
    "humanReviewed": false
  }
}
```

#### 3. .ofs.index.json (Directory-Level Index)

**Location**: Any directory containing source documents (`A/`, bidder subfolders, etc.)

**Purpose**: Operational index for file discovery, parser coverage tracking, and document-level metadata attachment.

**Example Structure**:
```json
{
  "files": [
    {
      "name": "document_name.pdf",
      "size": 12345,
      "hash": "md5_hash",
      "parsers": {
        "status": "completed",
        "det": ["docling", "pdfplumber"],
        "default": "docling"
      },
      "meta": {
        "kategorie": "Eignungsnachweise",
        "name": "Document display name"
      }
    }
  ],
  "directories": [],
  "timestamp": 1234567890.123
}
```

**Key Fields**:
- `size`: Original file size in bytes for reference
- `hash`: MD5 hash of file content for integrity verification
- `parsers.status`: Current parsing status (`completed`, `pending`, `failed`)
- `parsers.det`: Available parsers for this file
- `meta.kategorie`: Document category (e.g., "Berufliche Zuverlässigkeit", "Eignungsnachweise")
- `meta.name`: Human-readable display name for the document

#### 4. filename.ext.meta.json (Document-Specific Metadata)

**Location**: Next to individual documents

**Purpose**: Stores metadata specific to individual documents.

**Example Structure**:
```json
{
  "aussteller": "Wiener Wohnen Hausbetreuung GmbH",
  "beschreibung": "Das Dokument wird im Titel und im Einleitungstext explizit als 'Leitfaden zum Angebot' bezeichnet und dient dazu, Bieter durch die Ausschreibung zu führen und beim Aufbau des Angebots zu unterstützen.",
  "metadaten": []
}
```

### Metadata Processing Flow

1. Raw documents enter `A/` or `B/<Bidder>/`
2. Conversions populate `md/` and update `.ofs.index.json` (parser coverage)
3. Project-level synthesis produces/updates `projekt.meta.json`
4. Criteria extraction pipeline outputs `kriterien.meta.json` referencing authoritative source documents
5. Downstream enrichment augments `meta` blocks inside the index and/or adds structured objects to `projekt.meta.json`

## Configuration

OFS uses a priority-based configuration system to load settings:

1. **Environment variables** (highest priority)
2. **Local config file** (`./ofs.config.json`)
3. **User home config file** (`~/.ofs.config.json`)
4. **Default values** (lowest priority)

### Configurable Options

- `BASE_DIR`: Base directory for OFS structure (default: `.dir`)
- `INDEX_FILE`: Name of index files (default: `.ofs.index.json`)
- `METADATA_SUFFIX`: Suffix for metadata files (default: `.meta.json`)

### Environment Variables

```bash
# Override BASE_DIR
export OFS_BASE_DIR="/path/to/custom/dir"

# Override INDEX_FILE
export OFS_INDEX_FILE=".custom.index.json"

# Override METADATA_SUFFIX
export OFS_METADATA_SUFFIX=".custom.meta.json"
```

## WebDAV Support

OFS supports remote storage through WebDAV for seamless access and synchronization. WebDAV paths are constructed from user-configured parameters:

- **Base URL** (e.g., `https://webdav.example.com`)
- **Path prefix** (e.g., `/remote/disk`)
- **Full path example**: `https://webdav.example.com/remote/disk/2025-04 Lampen/A/2024_06001_AAB_EV.pdf`

This allows remote access to the entire OFS structure while maintaining the same organizational principles.

## Best Practices

### Project Organization
- Always place new projects at the root level
- Use descriptive project names that include dates or reference numbers
- Archive completed projects to maintain a clean active workspace
- Maintain consistent naming conventions across projects

### Document Processing
- Use processing workers to generate `md/` content automatically
- Ensure all supported file types are properly indexed
- Keep original documents intact while storing processed versions in `md/` subdirectories
- Regularly update index files to reflect current document status

### Metadata Management
- Update metadata JSON files via API endpoints for consistency
- Maintain traceability by preserving `aabFileName` references in criteria files
- Use structured keywords in `schlagworte` for better searchability
- Implement validation checks before deployment (see Validation Checklist below)

### Validation Checklist

Before deploying or archiving projects, ensure:

| Check | File | Condition |
|-------|------|-----------|
| Project identity present | projekt.meta.json | `projektName` & `referenznummer` non-empty |
| Core deadlines consistent | projekt.meta.json | `bieterabgabe` >= today or flagged archived |
| AAB reference resolvable | kriterien.meta.json | `aabFileName` exists in index `files` list |
| Parser coverage threshold | .ofs.index.json | Required minimum parser(s) executed |
| Categorization completeness | .ofs.index.json | All `meta.kategorie` populated (or queued) |

## Tooling and Future Enhancements

### Current Tooling Support
- **Python API**: Complete programmatic access to OFS structure and metadata
- **CLI Interface**: Command-line tools for index management and document operations
- **WebDAV Integration**: Remote storage and synchronization capabilities
- **Processing Workers**: Automated document conversion and metadata extraction

### Planned Enhancements
- **Enhanced Search**: Full-text search across processed Markdown content
- **Validation Tools**: Automated consistency checking and error reporting
- **Migration Utilities**: Tools for upgrading OFS structures and metadata formats
- **Integration APIs**: Enhanced support for external document management systems
- **Performance Optimization**: Improved indexing and caching mechanisms

### Integration Considerations
- OFS is designed to work with existing document management workflows
- The structure supports both manual and automated document processing
- Metadata files enable rich querying and filtering capabilities
- The system scales from small projects to large enterprise deployments

## Development

This package is currently in early development. The main functionality includes:

- `get_path(name)`: Returns a path for a given name using configured BASE_DIR
- `get_paths_json(name)`: Retrieves paths for a name in JSON format.
- `list_projects_json()`: Retrieves all projects in JSON format.
- Configuration system with file and environment variable support.
- CLI interface for basic operations
- Extensible structure for future OFS features

## Requirements

- Python >= 3.12

## Project Structure

```
ofs/
├── ofs/
│   ├── __init__.py
│   ├── core.py
│   └── cli.py
├── tests/
├── docs/
├── setup.py
├── README.md
└── PRD.md
```

## legacy code

we are trying to rebuild and replicate certain functions from strukt2meta and from pdf2md library

`pdf --index un` stores unparsed and unkategorized items into a file called un_items.json

````shell
pdf2md .disk --index un --recursive --json```
````

```
Found 119 unparsed or uncategorized item(s).
Unparsed and uncategorized items list saved to: .disk/un_items.json
```

strukt2umeta unlist kategorizes 119 items from the list and updates the ofs index.

```bash
strukt2meta unlist 119 .disk2/un_items.json
```
