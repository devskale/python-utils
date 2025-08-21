# OFS (Opinionated Filesystem)

A comprehensive Python package for managing opinionated filesystem structures designed to organize tender documents (Ausschreibungsdokumente) and bidder documents (Bieterdokumente) in a standardized, efficient manner. This structure facilitates AI-assisted legal analysis, document processing, and metadata management.

## Key Concepts

- **Ausschreibungsdokumente**: Documents created and published by the contracting authority to inform potential bidders about the tender. They include performance descriptions, participation conditions, contract terms, and deadlines.
- **Bieterdokumente**: Documents submitted by bidders, including offers, price sheets, suitability proofs, and possibly concepts or technical solutions.
- **Index Files**: `.ofs.index.json` files that track document metadata, parsing status, and categorization.
- **Metadata Files**: JSON files containing project information, criteria, and document metadata.

The structure supports local and remote storage (e.g., via WebDAV) and is optimized for processing pipelines like PDF to Markdown conversion with comprehensive indexing and metadata management.

## Supported File Types

The system supports the following file types for documents:

- PDF (text-based or scanned)
- Office documents (docx, xlsx, pptx)
- Text files (txt)
- Images (jpg, jpeg, png)

Processed outputs include Markdown (.md) and JSON metadata.

## Installation

```bash
# Install from source (development)
cd /path/to/ofs
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

## Configuration

OFS uses a hierarchical configuration system that loads settings from multiple sources in priority order:

1. **Environment variables** (highest priority)
2. **Local config**: `ofs.config.json` (in the current working directory)
3. **User config**: `~/.ofs/config.json` (in the user's home directory)
4. **Default values** (lowest priority)

### Configuration Options

```json
{
  "BASE_DIR": ".dir",
  "INDEX_FILE": ".ofs.index.json",
  "METADATA_SUFFIX": ".meta.json"
}
```

- **BASE_DIR**: Root directory for OFS operations (default: `.dir`)
- **INDEX_FILE**: Name of index files (default: `.ofs.index.json`)
- **METADATA_SUFFIX**: Suffix for metadata files (default: `.meta.json`)

### Environment Variables

You can override any configuration setting using environment variables:

```bash
export OFS_BASE_DIR="/path/to/documents"
export OFS_INDEX_FILE="custom_index.json"
export OFS_METADATA_SUFFIX=".metadata.json"
```

## Usage

### Command Line Interface

OFS provides a comprehensive CLI for managing and navigating your document structure:

#### Path Operations
```bash
# Get path for a project or bidder
ofs get-path "ProjectName"
ofs get-path "BidderName"

# Get OFS root directory
ofs root
```

#### Listing and Discovery
```bash
# List all available items (projects, bidders, files)
ofs list

# List all projects
ofs list-projects

# List all bidders in a specific project
ofs list-bidders "ProjectName"

# Find a specific bidder within a project
ofs find-bidder "ProjectName" "BidderName"

# List documents for a specific bidder
ofs list-docs "ProjectName" "BidderName"
```

#### Document Operations
```bash
# Read a specific document
ofs read-doc "ProjectName" "BidderName" "document.pdf"

# Display directory tree structure
ofs tree
```

## CLI Usage

The package provides a comprehensive command-line interface:

### Path Resolution
```bash
# Get path for a project or bidder name
ofs get-path "2025-04 Lampen"
ofs get-path "Lampion GmbH"
```

### Project Management
```bash
# List all projects
ofs list-projects

# List bidders in a project
ofs list-bidders "2025-04 Lampen"

# Find specific bidder in project
ofs find-bidder "2025-04 Lampen" "Lampion GmbH"
```

### Document Listing
```bash
# List project documents (from A/ folder) - minimal view
ofs list-docs "2025-04 Lampen"

# List project documents with full metadata
ofs list-docs "2025-04 Lampen" --meta

# List bidder documents - minimal view
ofs list-docs "2025-04 Lampen@Lampion GmbH"

# List bidder documents with full metadata
ofs list-docs "2025-04 Lampen@Lampion GmbH" --meta

# Get detailed information for specific document
ofs list-docs "2025-04 Lampen@Lampion GmbH@document.pdf"
```

### Tree Visualization
```bash
# Show complete tree structure
ofs tree

# Show only directories (no documents)
ofs tree -d
```

### Criteria Management
```bash
# Show next unproven criterion
ofs kriterien "2025-04 Lampen" pop

# Show next unreviewed criterion for a bidder audit (zustand==synchronisiert)
ofs kriterien "2025-04 Lampen" pop --bidder "Lampion GmbH"

# Display criteria organized by category and type
ofs kriterien "2025-04 Lampen" tree

# Get specific criterion by ID
ofs kriterien "2025-04 Lampen" tag "EIG_001"

# List all available criterion tags
ofs kriterien "2025-04 Lampen" tag

# Synchronize project criteria into bidder audit files (create/update/remove)
ofs kriterien-sync "2025-04 Lampen"                 # all bidders of project
ofs kriterien-sync "2025-04 Lampen" "Lampion GmbH"  # single bidder only

# Append audit events (Review / Final / Reset)
# (Requires prior sync so that the criterion exists in audit.json)
ofs kriterien-audit ki "2025-04 Lampen" "Lampion GmbH" F_FORM_001          # KI-Prüfung
ofs kriterien-audit mensch "2025-04 Lampen" "Lampion GmbH" F_FORM_001      # Menschliche Prüfung
ofs kriterien-audit freigabe "2025-04 Lampen" "Lampion GmbH" F_FORM_001    # Freigabe (final)
ofs kriterien-audit ablehnung "2025-04 Lampen" "Lampion GmbH" F_FORM_001   # Ablehnung (final)
ofs kriterien-audit reset "2025-04 Lampen" "Lampion GmbH" F_FORM_001       # Reset Segment (z.B. nach Statusänderung)
ofs kriterien-audit show  "2025-04 Lampen" "Lampion GmbH" F_FORM_001       # Verlauf & Zustand anzeigen
```

### Index Management
```bash
# Create index for directory
ofs index create "/path/to/directory"

# Update existing index
ofs index update "/path/to/directory"

# Clear index data
ofs index clear "/path/to/directory"

# Show index statistics
ofs index stats "/path/to/directory"
```

### Configuration
```bash
# Show current configuration
ofs config
```

### Python API

```python
import ofs

# Path resolution
path = ofs.get_path("2025-04 Lampen")  # Find project or bidder
print(f"Path: {path}")

# Project management
projects = ofs.list_projects()  # List all projects
bidders = ofs.list_bidders("2025-04 Lampen")  # List bidders in project
bidder_path = ofs.find_bidder_in_project("2025-04 Lampen", "Lampion GmbH")

# Document management
# List project documents (minimal view)
project_docs = ofs.list_project_docs_json("2025-04 Lampen")

# List project documents with full metadata
project_docs_full = ofs.list_project_docs_json("2025-04 Lampen", include_metadata=True)

# List bidder documents
bidder_docs = ofs.list_bidder_docs_json("2025-04 Lampen", "Lampion GmbH")

# Get specific document details
doc_details = ofs.get_bidder_document_json("2025-04 Lampen", "Lampion GmbH", "document.pdf")

# Read document content with intelligent parser selection
content = ofs.read_doc("2025-04 Lampen@Lampion GmbH@document.pdf")
# Or specify a parser
content = ofs.read_doc("2025-04 Lampen@Lampion GmbH@document.pdf", parser="docling")

# Tree structure
tree_data = ofs.generate_tree_structure()  # Full tree
tree_dirs_only = ofs.generate_tree_structure(directories_only=True)
tree_string = ofs.print_tree_structure()  # Formatted string

# Criteria management
kriterien_file = ofs.find_kriterien_file("2025-04 Lampen")
if kriterien_file:
    kriterien_data = ofs.load_kriterien(kriterien_file)
    unproven = ofs.get_unproven_kriterien(kriterien_data)
    tree = ofs.build_kriterien_tree(kriterien_data)
    specific = ofs.get_kriterien_by_tag(kriterien_data, "EIG_001")

# Index management
ofs.create_index("/path/to/directory")
ofs.update_index("/path/to/directory")
index_data = ofs.load_index_from_directory("/path/to/directory")

# JSON API endpoints (for web interfaces)
paths_data = ofs.get_paths_json("project-name")
projects_json = ofs.list_projects_json()
bidders_json = ofs.list_bidders_json("2025-04 Lampen")
kriterien_pop = ofs.get_kriterien_pop_json("2025-04 Lampen")
kriterien_tree = ofs.get_kriterien_tree_json("2025-04 Lampen")

# Configuration
config = ofs.get_config()
base_dir = ofs.get_base_dir()
print(f"Base directory: {base_dir}")
```

### Programmatic API Parity & High-Level Wrappers

The module `ofs.api` provides friendly, idempotent wrapper functions that mirror the CLI semantics. They return structured Python data (dicts / lists) and raise exceptions for hard errors instead of printing.

#### Quick Import
```python
from ofs.api import (
  get_path_info,
  list_items,
  list_projects,
  list_bidders_for_project,
  find_bidder,
  docs_list,
  read_document,
  kriterien_pop,
  kriterien_sync,
  kriterien_audit_event,
)
```

#### CLI → API Mapping

| CLI Command | Purpose | API Wrapper (ofs.api) |
|-------------|---------|------------------------|
| `ofs get-path <name>` | Resolve project / bidder paths & variants | `get_path_info(name)` |
| `ofs list` | List mixed items (projects / bidders / files) | `list_items()` |
| `ofs list-projects` | List all project names | `list_projects()` |
| `ofs list-bidders <project>` | List bidder names | `list_bidders_for_project(project)` |
| `ofs find-bidder <project> <bidder>` | Locate bidder directory | `find_bidder(project, bidder)` |
| `ofs list-docs <identifier>` | List documents (project / bidder / single) | `docs_list(identifier, meta=False)` |
| `ofs read-doc <identifier>` | Read document (content or JSON) | `read_document(identifier, parser=None, as_json=False)` |
| `ofs tree` | Structure (string / model) | `generate_tree_structure()`, `print_tree_structure()` (direct in `ofs`) |
| `ofs kriterien <proj> pop` | Next unproven project criteria | `kriterien_pop(project, limit)` |
| `ofs kriterien <proj> pop --bidder B` | Next unreviewed bidder audit entries | `kriterien_pop(project, bidder=B, limit=N)` |
| `ofs kriterien <proj> tree` | Criteria tree summary | `get_kriterien_tree_json(project)` |
| `ofs kriterien <proj> tag [ID]` | Criteria tag(s) | `get_kriterien_tag_json(project, tag_id=None|ID)` |
| `ofs kriterien-sync <proj> [bidder]` | Sync criteria → audit | `kriterien_sync(project, bidder=None)` |
| `ofs kriterien-audit <event>` | Append / show audit events | `kriterien_audit_event(event, project, bidder, kriterium_id, ...)` |
| `ofs index create|update|clear|stats|un` | Index management | `create_index`, `update_index`, `clear_index`, `print_index_stats`, `generate_un_items_list` (direct in `ofs`) |

#### Criteria Pop (Project vs Bidder)
```python
from ofs.api import kriterien_pop

# Project-level: shows source criteria whose pruefung.status is None
proj_pop = kriterien_pop("2025-04 Lampen", limit=3)
for k in proj_pop["kriterien"]:
  print("PROJECT OPEN:", k["id"], k.get("pruefung", {}).get("status"))

# Bidder-level: shows audit entries with zustand == synchronisiert (not yet reviewed)
bid_pop = kriterien_pop("2025-04 Lampen", bidder="Lampion GmbH", limit=2)
for k in bid_pop["kriterien"]:
  print("BIDDER OPEN:", k["id"], k["zustand"])  # fields reduced to stable surface
```

#### Full Kriterien Sync & Audit Flow
```python
from ofs.api import kriterien_sync, kriterien_audit_event, kriterien_pop

# 1. Ensure bidder audit has all criteria
sync_summary = kriterien_sync("2025-04 Lampen", bidder="Lampion GmbH")
print(sync_summary)

# 2. Get the next two unreviewed (bidder-level) criteria
next_two = kriterien_pop("2025-04 Lampen", bidder="Lampion GmbH", limit=2)
first_id = next_two["kriterien"][0]["id"]

# 3. Record KI review
ki_result = kriterien_audit_event("ki", "2025-04 Lampen", "Lampion GmbH", first_id, akteur="ki-pipeline", ergebnis="score:0.82")
print(ki_result)

# 4. Human review & final decision
mensch_result = kriterien_audit_event("mensch", "2025-04 Lampen", "Lampion GmbH", first_id, akteur="reviewer")
final_result = kriterien_audit_event("freigabe", "2025-04 Lampen", "Lampion GmbH", first_id, akteur="reviewer")

# 5. Inspect full timeline
timeline = kriterien_audit_event("show", "2025-04 Lampen", "Lampion GmbH", first_id)
print(timeline["zustand"], timeline["events_total"])  # freigegeben
```

#### Handling Status Changes (Reset Logic)
If the source `kriterien.json` changes the status of a criterion after it was final (freigegeben/abgelehnt), a subsequent sync will automatically insert a `reset` + new `kopiert` event pair before further processing.

```python
# After editing kriterien.json (e.g., status change) run another sync:
resync = kriterien_sync("2025-04 Lampen", bidder="Lampion GmbH")
# The impacted audit entry's verlauf now contains ... freigabe, reset, kopiert
```

#### Document Lookup Convenience
```python
from ofs.api import docs_list, read_document

# Project-level documents summary
project_docs = docs_list("2025-04 Lampen")

# Bidder-level documents with metadata
bidder_docs = docs_list("2025-04 Lampen@Lampion GmbH", meta=True)

# Single document (bidder)
single = docs_list("2025-04 Lampen@Lampion GmbH@angebot.pdf")

# Read content (best parser auto-selected) or JSON detail
content = read_document("2025-04 Lampen@Lampion GmbH@angebot.pdf")
detail = read_document("2025-04 Lampen@Lampion GmbH@angebot.pdf", as_json=True)
```

#### Error Handling Pattern
All high-level API wrappers raise `RuntimeError` or `ValueError` for invalid state (e.g., missing project, bidder, or criterion). Wrap calls in try/except for robust pipelines:
```python
try:
  sync_summary = kriterien_sync("2025-04 Lampen", bidder="Lampion GmbH")
except RuntimeError as e:
  # log / fallback
  print("Sync failed:", e)
```

#### Stable Return Shapes (Selected)
- `kriterien_sync()` → `{ project, mode, count_bidders, results:[ {bidder, created, updated, removed, unchanged, wrote_file, total_entries} ] }`
- `kriterien_pop(project)` (project scope) → uses original source schema entries (unmodified)
- `kriterien_pop(project, bidder=...)` (bidder scope) → each entry: `{ id, status, prio, zustand }`
- `kriterien_audit_event('show', ...)` → `{ project, bidder, id, zustand, status, prio, bewertung, events_total, verlauf:[...] }`
- `kriterien_audit_event(<event>, ...)` → `{ project, bidder, id, event, zustand, events_total }` or `{ ..., skipped: True, reason: 'duplicate' }`

#### Idempotence Guarantees
- Re-running `kriterien_sync` without source changes writes nothing (`wrote_file=False`).
- `kriterien_audit_event` dedupes identical consecutive events unless `force_duplicate=True` (CLI: `--force-duplicate`).
- Bidder-level `kriterien_pop` only surfaces entries still at `zustand == synchronisiert`.

#### When to Use Which Layer
| Layer | Use Case | Pros | Cons |
|-------|----------|------|------|
| CLI | Manual ops, shell scripting | Fast to try, human-friendly | Parsing output for automation |
| `ofs` (core exports) | Low-level integration, custom processing | Full flexibility | Some assembly required |
| `ofs.api` | Rapid orchestration, service endpoints | Stable shapes, less boilerplate | Slight abstraction overhead |

> Tip: For long-running services prefer `ofs.api` for stability, and fall back to core functions only when you need deeper control (e.g., custom audit mutation logic).

---

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
  - **projekt.json**: Project metadata file
  - **kriterien.json** (optional): Criteria metadata
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
│   │   ├── audit.json               # Bidder kriterien audit
│   │   ├── Lampion/                   # Specific bidder folder
│   │   │   ├── 1completed-austrian-document.pdf   # Original bidder document
│   │   │   └── md/                    # Markdown conversions
│   │   │       ├── 1completed-austrian-document.docling.md
│   │   │       └── 1completed-austrian-document/
│   │   │           └── 1completed-austrian-document.marker.md
│   │   └── archive/                   # Archived bidder folders
│   │       └── Lampion2/              # Archived version of bidder
│   ├── projekt.json              # Project metadata
│   └── kriterien.json            # Extracted criteria
├── A-TEST/                            # Another project
│   ├── A/
│   ├── B/
│   └── projekt.json
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

#### 1. projekt.json (Project-Level Metadata)

**Location**: Project root (e.g., `2025-04 Lampen/projekt.json`)

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

#### 2. kriterien.json (Projekt-Kriterien & Bieterdokument-Anforderungen)

**Location**: Project root (created when criteria & bidder document extraction runs successfully)

**Purpose**: Einheitliche, normalisierte Darstellung aller formal / eignungs- / zuschlagsrelevanten Anforderungen sowie der geforderten Bieterdokumente. Dient als Grundlage für:
- Compliance-Checks (Pflicht vs. Bedarfsfall)
- Angebots-Guidance (Welche Dokumente sind einzureichen?)
- Automatisierte Priorisierung / Prüf-Workflows
- Los-spezifische Auswertung (z.B. unterschiedliche Bewertung je Los)

**Top-Level Keys**:
1. `meta` – Metadaten & lose
2. `bdoks` – Strukturierte Liste geforderter Bieterdokumente
3. `ids` – Kanonische Kriterien-/Anforderungs-IDs (formal, eignung, zuschlag)

**Detailed Structure**:

```json
{
  "meta": {
    "schema_version": "<string>",
    "meta": {
      "auftraggeber": "<string>",
      "aktenzeichen": "<string>
      ", "lose": [
        {
          "nummer": "Los 1",
          "bezeichnung": "<Kurzname>",
          "beschreibung": "<Beschreibung>",
          "bewertungsprinzip": "Bestbieter|Billigstbieter|…"
        }
        /* weitere Lose */
      ]
    }
  },
  "bdoks": {
    "schema_version": "<string>",
    "bieterdokumente": [
      {
        "anforderungstyp": "Pflichtdokument|Bedarfsfall",
        "dokumenttyp": "Formblatt|Nachweis|Angebot|Zusatzdokument|…",
        "bezeichnung": "<Sprechender Titel>",
        "beilage_nummer": "Beilage 01" ,
        "beschreibung": "<Zweck / Inhalt>",
        "unterzeichnung_erforderlich": true,
        "fachliche_pruefung": false
      }
      /* weitere Dokumentanforderungen */
    ]
  },
  "ids": {
    "schema_version": "<string>",
    "kriterien": [
      {
        "id": "F_FORM_001",        
        "typ": "Formal|Eignung|Zuschlag",
        "kategorie": "Formale Anforderungen|Dokumentation|Fristen|…",
        "name": "<Kurzname>",
        "anforderung": "<Volltext / normative Anforderung>",
        "schwellenwert": "<z.B. 6 Monate|EUR 300.000,00|… oder null>",
        "gewichtung_punkte": 700,    // nur bei Zuschlagskriterien
        "dokumente": [ "Beilage 04", "Strafregisterbescheinigung" ],
        "geltung_lose": [ "alle" | "Los 1" ],
        "pruefung": {
          "status": "ja|ja.int|ja.ki|nein|halt|erfüllt|null",
          "bemerkung": null,
          "pruefer": null,
          "datum": null
        },
        "quelle": "Punkt 5.1. (3)"
      }
      /* weitere Kriterien */
    ]
  }
}
```

**Semantik der Bereiche**:
- `meta.meta.lose[]`: Definition & Bewertungsprinzip je Los (steuert spätere Scoring-Algorithmen)
- `bdoks.bieterdokumente[]`: Atomare Einreichungs-Anforderungen; kann 1:n zu Kriterien stehen (z.B. ein Formular deckt mehrere Kriterien ab)
- `ids.kriterien[]`: Normalisierte fachliche / formale / zuschlagsrelevante Anforderungen (einmalig referenzierbar über `id`)

**Feld-Erklärungen (Kriterien)**:
- `id`: Stabiler, kanonischer Schlüssel (präfix kodiert Bereich: F_=Formal, E_=Eignung, Z_=Zuschlag)
- `typ`: Grobklassifikation (steuert Auswertungspfade)
- `kategorie`: Feinere Gruppierung (z.B. "Nachweise", "Preis", "Fristen")
- `schwellenwert`: Numerischer oder textueller Schwellen-/Gültigkeitsparameter (oder `null`)
- `gewichtung_punkte`: Nur für Zuschlagskriterien (Preis/Qualität etc.); `null` sonst
- `dokumente[]`: Erwartete unterstützende Dokumente (Abgleich mit `bdoks.bieterdokumente.bezeichnung` oder Beilage-Nummern)
- `geltung_lose[]`: `alle` oder Liste konkreter Lose; bestimmt Filterung bei Los-spezifischer Ansicht
- `pruefung.status`: Aktueller (extrahierter / interim) Status (siehe Status-Matrix unten) – kann später von KI / Mensch überschrieben werden
- `quelle`: Textuelle Referenz auf Ursprungspassus (Rückverfolgbarkeit)

**Status-Werte (aktuell beobachtet)**:
| Wert      | Bedeutung Kurz | Typische Nutzung |
|-----------|----------------|------------------|
| `ja`      | Anforderung positiv erfüllt / zutreffend / muss eingehalten werden | Basis-Kennzeichnung Pflicht |
| `ja.int`  | Intern vorgeprüft (Interimszustand) | Kennzeichnung für menschliche Nachprüfung |
| `ja.ki`   | KI-basiert vorläufig als zutreffend markiert | Automatisches Pre-Labeling |
| `erfüllt` | Bereits nachweislich erfüllt | Abschluss einer Erfüllungsprüfung |
| `nein`    | Negativ / nicht zulässig / verletzt | Trigger für Risiko / Ausschluss |
| `halt`    | Angehalten / benötigt Klärung | Wartet auf zusätzliche Info |
| `null`    | Noch nicht klassifiziert | Default nach Extraktion |

Anmerkung: Die Statusdomäne ist bewusst textuell offen gehalten, um spätere Verfeinerung (z.B. `ja.doc`, `ja.rev1`) ohne Schema-Migration zu ermöglichen.

**Verknüpfungsmuster**:
- `dokumente[]` in Kriterien dienen als logische Erwartung; tatsächliche Einreichung erfolgt über den Bestand in `B/<Bieter>/` und kann mit Namen / Beilage-Nummern gematcht werden.
- Mehrere Kriterien können auf dasselbe Dokument verweisen (Reduktion Doppeleinreichungen).

**Validierungsideen (Future)**:
- Cross-Check: Jede `Beilage XX` in `kriterien.dokumente` sollte auch in `bdoks.bieterdokumente.bezeichnung` oder `beilage_nummer` vorkommen.
- Scoring: Summe aller `gewichtung_punkte` je Los ergibt maximale erreichbare Punktzahl für Qualitäts-/Preisdimensionen.
- Vollständigkeit: Für Pflicht-Kriterien ohne `pruefung.status` ∈ {`ja`, `erfüllt`} Warnung generieren.

**Minimal API Patterns** (Python):
```python
data = ofs.load_kriterien("/path/to/project/kriterien.json")
alle_kriterien = data["ids"]["kriterien"]
pflicht_docs = [d for d in data["bdoks"]["bieterdokumente"] if d["anforderungstyp"] == "Pflichtdokument"]
offene = [k for k in alle_kriterien if (k["pruefung"]["status"] in (None, "halt") )]
```

Diese aktualisierte Struktur ersetzt die frühere, vereinfachte `extractedCriteria`-Repräsentation.

### Bidder Audit / Kriterien-Sync

Der Synchronisationsprozess kopiert alle Kriterien-IDs aus `kriterien.json` in eine pro Bieter geführte Audit-Datei:  
`<Projekt>/B/<Bieter>/audit.json`

Ziele:
- Vollständige, idempotente Spiegelung aller IDs (auch solche ohne Status)
- Ereignisbasierter Verlauf statt starrer Statusfelder
- Nicht-destruktive Markierung entfernter IDs
- Grundlage für KI- / Mensch-Prüfungen und finale Entscheidungen

#### CLI
```
ofs kriterien-sync <Projekt>            # synchronisiert alle Bieter
ofs kriterien-sync <Projekt> <Bieter>   # nur ein Bieter
```
Mehrfacher Aufruf ohne Quelländerung ist idempotent (keine neuen Events / keine Dateiänderung).

#### audit.json – Schema (vereinfacht)
```json
{
  "meta": { "schema_version": "1.0-bieter-kriterien", "projekt": "2025-04 Lampen", "bieter": "Lampion GmbH" },
  "kriterien": [
    {
      "id": "F_FORM_001",
      "status": "ja",            // letzter übernommener Source-Status oder "entfernt"
      "prio": 5,                  // optional aus Quelle
      "bewertung": null,          // später: ok/fail/score/review-needed
      "audit": {
        "zustand": "geprueft",   // abgeleitet (siehe Algorithmus)
        "verlauf": [
          {"zeit": "...", "ereignis": "kopiert", "quelle_status": "ja"},
          {"zeit": "...", "ereignis": "ki_pruefung"},
          {"zeit": "...", "ereignis": "mensch_pruefung"},
          {"zeit": "...", "ereignis": "freigabe"}
        ]
      }
    }
  ]
}
```

#### Ereignisse
| Ereignis           | Bedeutung | Wirkung auf zustand |
|--------------------|-----------|---------------------|
| `kopiert`          | Erstmalige oder aktualisierte Übernahme aus Quelle | nur Basis (falls nichts Weiteres) → synchronisiert |
| `ki_pruefung`      | KI hat Kriterium vorbewertet | kann zustand zu geprueft heben |
| `mensch_pruefung`  | Menschliche Prüfung durchgeführt | kann zustand zu geprueft heben |
| `freigabe`         | Fachlich/final akzeptiert | zustand → freigegeben |
| `ablehnung`        | Final abgelehnt | zustand → abgelehnt |
| `reset`            | Finaler Zustand invalidiert (z.B. Source-Status geändert) | Segment neu ⇒ zurück auf synchronisiert/geprueft abhängig nachfolg. Events |
| `entfernt`         | Kriterium nicht mehr in Quelle vorhanden | keine Änderung des vorhandenen zustand |

#### Zustandsableitung (finale Logik)
Der Zustand wird nicht direkt gespeichert, sondern nach jedem Event aus dem Verlauf abgeleitet:

1. Der Verlauf wird in Segmente geteilt – ein `reset` beginnt ein neues Segment und löscht die Wirkung vorheriger Events.
2. Innerhalb des aktuellen Segments gilt Priorität:
   - Letztes finales Event (`freigabe` oder `ablehnung`) gewinnt → `freigegeben` / `abgelehnt`.
   - Sonst wenn mindestens ein Prüfungs-Event (`ki_pruefung` oder `mensch_pruefung`) vorkam → `geprueft`.
   - Sonst → `synchronisiert`.
3. `entfernt` beeinflusst den Zustand nicht; `reset` löscht vorangegangene final/review-Wirkungen.

Pseudocode (vereinfacht):
```text
state = synchronisiert
segment: track last_final, last_review
for event in events:
  if event == reset: clear segment trackers
  elif event in {freigabe, ablehnung}: last_final = event
  elif event in {ki_pruefung, mensch_pruefung}: last_review = event
if last_final: state = (freigabe→freigegeben | ablehnung→abgelehnt)
elif last_review: state = geprueft
else: state = synchronisiert
```

#### Updates & Removals
- Status-/Prio-Änderung in Quelle → neues `kopiert` Event; falls zuvor final (freigegeben/abgelehnt) → zusätzlich `reset` davor.
- Kriterium fehlt in Quelle → `status` wird auf `entfernt` gesetzt + einmaliges `entfernt` Event (bewertung bleibt erhalten).

#### Idempotenz
Ein erneuter Lauf ohne Quelländerungen erzeugt:
- Keine zusätzlichen Events
- Keine Dateiänderung (Write-Skip)

#### Erweiterungs-Pfade (geplant / optional)
- `bewertung` Ausdifferenzierung (score, flag review-needed)
- Hash-basierter Skip (Performance)
- CLI-Unterkommandos zum Hinzufügen manueller Events (`freigabe`, `ablehnung`, etc.)

#### Beispiel CLI Flow
```bash
# Initial sync aller Bieter
ofs kriterien-sync "2025-04 Lampen"

# Einzelnen Bieter erneut synchronisieren (nur Änderungen geschrieben)
ofs kriterien-sync "2025-04 Lampen" "Lampion GmbH"

# Nach Änderung in kriterien.json (Statuswechsel) erneut sync → reset + kopiert Events bei betroffenen IDs
ofs kriterien-sync "2025-04 Lampen" "Lampion GmbH"
```

#### 3. .ofs.index.json (Directory-Level Index)

**Location**: Any directory containing source documents (`A/`, bidder subfolders, etc.)

**Purpose**: Operational index for file discovery, parser coverage tracking, and document-level metadata attachment.

**Example Structure**:
```json
{
  "timestamp": 1234567890,
  "files": [
    {
      "name": "document_name.pdf",
      "size": 12345,
      "modified": 1234567890,
      "hash": "sha256_hash",
      "extension": ".pdf",
      "parsers": {
        "det": ["docling", "pdfplumber", "marker"],
        "default": "docling",
        "status": ""
      },
      "meta": {
        "kategorie": "Eignungsnachweise",
        "name": "Document display name"
      }
    }
  ],
  "directories": [
    {
      "name": "subdirectory",
      "size": 4096,
      "modified": 1234567890,
      "hash": "directory_hash"
    }
  ]
}
```

**Key Fields**:
- `timestamp`: Index creation/update timestamp
- `size`: Original file size in bytes for reference
- `modified`: File modification timestamp
- `hash`: SHA-256 hash of file content for integrity verification
- `extension`: File extension for type identification
- `parsers.det`: Available parsers detected for this file (based on `md/` folder contents)
- `parsers.default`: Default parser selected based on hierarchy (docling > marker > llamaparse > pdfplumber)
- `parsers.status`: Current parsing status (empty string by default)
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
3. Project-level synthesis produces/updates `projekt.json`
4. Criteria extraction pipeline outputs `kriterien.json` referencing authoritative source documents
5. Downstream enrichment augments `meta` blocks inside the index and/or adds structured objects to `projekt.json`

## Advanced Configuration

For advanced use cases, you can override configuration settings using environment variables:

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
| Project identity present | projekt.json | `projektName` & `referenznummer` non-empty |
| Core deadlines consistent | projekt.json | `bieterabgabe` >= today or flagged archived |
| AAB reference resolvable | kriterien.json | `aabFileName` exists in index `files` list |
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

This package provides comprehensive functionality for managing OFS (Opinionated Filesystem) structures. The main functionality includes:

### Core Functions
- `get_path(name)`: Returns a path for a given name using intelligent search algorithm
- `get_paths_json(name)`: Retrieves paths for a name in JSON format
- `list_projects()`: List all projects (AUSSCHREIBUNGNAME)
- `list_projects_json()`: Retrieves all projects in JSON format
- `list_bidders(project)`: List bidders in a specific project
- `find_bidder_in_project(project, bidder)`: Locate specific bidder within project

### Document Management
- `list_project_docs_json(project, include_metadata=False)`: List documents in project A/ folder
- `list_bidder_docs_json(project, bidder, include_metadata=False)`: List bidder documents
- `get_bidder_document_json(project, bidder, filename)`: Get detailed document information
- `read_doc(identifier, parser=None)`: Read document content with intelligent parser selection

### Tree Structure
- `generate_tree_structure(directories_only=False)`: Generate structured tree data
- `print_tree_structure(directories_only=False)`: Format tree for display

### Criteria Management
- `load_kriterien(file_path)`: Load criteria from JSON file
- `find_kriterien_file(project)`: Find criteria file for project
- `get_unproven_kriterien(data)`: Get criteria that haven't been proven
- `build_kriterien_tree(data)`: Build hierarchical criteria structure
- `get_kriterien_by_tag(data, tag_id)`: Get specific criterion by ID

### Index Management
- `create_index(directory)`: Create index for directory
- `update_index(directory)`: Update existing index
- `clear_index(directory)`: Clear index data
- `load_index_from_directory(directory)`: Load index from directory

### Configuration System
- File-based configuration (`ofs.config.json`)
- Environment variable support (`OFS_BASE_DIR`, `OFS_INDEX_FILE`, `OFS_METADATA_SUFFIX`)
- Intelligent defaults with `.dir` as BASE_DIR

### CLI Interface
Comprehensive command-line interface with commands for:
- Path resolution (`ofs get-path <name>`)
- Project management (`ofs list-projects`, `ofs list-bidders <project>`)
- Document listing (`ofs list-docs <project>`, `ofs list-docs <project@bidder>`)
- Tree visualization (`ofs tree`, `ofs tree -d`)
- Criteria management (`ofs kriterien <project> pop|tree|tag`)
- Index operations (`ofs index create|update|clear`)

## Requirements

- Python >= 3.12

## Project Structure

```
ofs/
├── ofs/
│   ├── __init__.py          # Package initialization and exports
│   ├── __main__.py          # Module execution support
│   ├── core.py              # Backward compatibility aggregator
│   ├── paths.py             # Path resolution and navigation
│   ├── docs.py              # Document listing and reading
│   ├── tree.py              # Tree structure generation
│   ├── kriterien.py         # Criteria management
│   ├── index.py             # Index management
│   ├── config.py            # Configuration system
│   ├── cli.py               # Command-line interface
│   └── logging.py           # Logging utilities
├── tests/                   # Comprehensive test suite
├── docs/                    # Documentation
├── setup.py                 # Package configuration
├── README.md               # This file
└── PRD.md                  # Product requirements document
```

## Architecture and Design

### Module Decomposition

OFS has been designed with a modular architecture for maintainability and extensibility:

- **`ofs/core.py`**: Backward compatibility aggregator that imports and re-exports all functions
- **`ofs/paths.py`**: Path resolution, project/bidder discovery, and OFS navigation
- **`ofs/docs.py`**: Document listing, metadata handling, and content reading
- **`ofs/tree.py`**: Directory tree structure generation and visualization
- **`ofs/kriterien.py`**: Criteria management and evaluation system
- **`ofs/index.py`**: Index file creation, updating, and management
- **`ofs/config.py`**: Configuration system with file and environment variable support
- **`ofs/cli.py`**: Comprehensive command-line interface

### Integration with Processing Pipelines

- **Index Management**: OFS maintains `.ofs.index.json` files that track document parsing status and available parsers
- **Metadata Processing**: Project and document metadata is managed through structured JSON files
- **Document Processing**: Support for multiple parsers (docling, pdfplumber, marker, llamaparse) with intelligent selection
- **Parser Detection**: Automatically detects available parsers by scanning `md/` subdirectories
- **Content Reading**: Intelligent content extraction from pre-processed Markdown files

### Backward Compatibility

- **Zero Breaking Changes**: All existing APIs are preserved through the `core.py` aggregator
- **Legacy Index Support**: Continues to work with existing `.ofs.index.json` files for document indexing and metadata management
- **Gradual Migration**: Supports both old and new metadata formats during transition periods
