# Opinionated Filesystem (OFS) - Structure

## Introduction

In the context of **kontext.one**, the opinionated filesystem (OFS) structure is designed to organize tender documents (Ausschreibungsdokumente) and bidder documents (Bieterdokumente) in a standardized, efficient manner. This structure facilitates AI-assisted legal analysis, ensuring modularity, easy navigation, and integration with processing tools.

- **Ausschreibungsdokumente**: Documents created and published by the contracting authority to inform potential bidders about the tender. They include performance descriptions, participation conditions, contract terms, and deadlines.
- **Bieterdokumente**: Documents submitted by bidders, including offers, price sheets, suitability proofs, and possibly concepts or technical solutions.

The structure supports local and remote storage (e.g., via WebDAV) and is optimized for processing pipelines like PDF to Markdown conversion.

## Supported Filetypes

The system supports the following file types for documents:

- PDF (text-based or scanned)
- Office documents (docx, xlsx, pptx)
- Text files (txt)
- Images (jpg, jpeg, png)

Processed outputs include Markdown (.md) and JSON metadata.

## Directory Structure

### Top-Level Structure

The root directory (e.g., `/disk/`) contains active tender project folders and an archive:

- Project Folder (named after the tender, e.g., `2025-04 Lampen` or `A-TEST`):
  - A/: Directory for tender documents (Ausschreibungsdokumente).
    - Contains original files (PDFs, DOCX, etc.).
    - md/: Subdirectory for Markdown conversions of tender documents.
      - Includes converted .md files and subdirectories for extracted content (e.g., images from PDFs).
  - B/: Directory for bidder documents (Bieterdokumente).
    - BIETERNAME/ (e.g., `Lampion`): Subdirectory for each bidder's documents.
      - Original bidder files.
      - md/: Markdown conversions of bidder documents.
      - archive/: Holds archived versions of bidder directories.
  - projekt.meta.json: Project metadata file (see Reserved Filenames).
  - kriterien.meta.json (optional): Criteria metadata (see Reserved Filenames).
- archive/: Directory for archived projects.
  - Contains moved project folders (e.g., archived `Ausschreibungsname`).

Additionally, index files like `.pdf2md_index.json` may appear at various levels to track conversions.

### Example from `/disk/`

Based on the provided tree:

- `2025-04 Lampen/`
  - `A/` with original files and `md/` containing conversions (e.g., `2024_06001_AAB_EV.docling.md`, extracted images).
  - `B/` with `Lampion/` containing bidder files and `md/` conversions.
  - `projekt.meta.json`
- `A-TEST/`
  - Similar structure with `A/`, `B/`, `projekt.meta.json`
- Other projects like `ATU1/`, `rasenmaeher/` follow the same pattern.

This structure ensures separation between tender and bidder data, with processed versions isolated in `md/` subdirectories.

## Reserved Directory Names

These directories have specific purposes and should not be used for other content:

- **A**: Exclusively for tender project documents.
- **B**: Exclusively for bidder documents.
- **md**: Contains Markdown-converted versions of documents and extracted assets (e.g., images from PDFs).
- **proc**: (Future) For other processed document versions (e.g., anonymized or analyzed outputs).
- **archive**: For archiving projects or sub-elements (e.g., old bidder submissions).

## Reserved Filenames

Certain filenames are reserved for system-generated content:

- **md/filename_PROCESSOR.md**: Markdown-converted version of the source document. `_PROCESSOR` indicates the converter used (e.g., `docling`, `pdfplumber`, `marker` for scanned PDFs).
- **md/filename/**: A subdirectory for extracted contents from the source file, such as images (`_page_X_Picture_Y.jpeg`) or additional .md files.
- **PROJEKTNAME.md** (e.g., in project root): Contains automatically extracted information about the project, such as summaries or key details from documents.
- **projekt.meta.json** (in project root):
  - Purpose: Stores comprehensive metadata about the project and its documents.
  - Content: Includes fields like vergabestelle, adresse, projektName, startDatum, bieterabgabe, projektStart, endDatum, beschreibung, referenznummer, schlagworte, sprache, dokumentdatum, selectedParser, metadaten (array).
  - Example structure:
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
      "schlagworte": "Ausschreibung, Vergabeverfahren, Offenes Verfahren, Oberschwellenbereich, BVergG 2018, Rahmenvertrag, Lieferauftrag, Leuchten, Lichtmasten, Ausleger, Wiener Wohnen Hausbetreuung GmbH, Wien, ISO-Zertifizierung, Lieferfrist, Eignung, Leistungsfähigkeit, Bonitätsranking, Betriebshaftpflichtversicherung",
      "sprache": "Deutsch",
      "dokumentdatum": "2025-07-31",
      "selectedParser": null,
      "metadaten": []
    }
    ```
  - Tracks integrity and changes for auditing.
- **kriterien.meta.json** (in project root):
  - Purpose: Metadata for extracted criteria (Zuschlagskriterien) from tender documents.
  - Content: JSON structure with extractedCriteria (including eignungskriterien, zuschlagskriterien, subunternehmerregelung, formale_anforderungen), extractionTimestamp, extractionMethod, aabFileName, lastModified, version, reviewStatus.
  - Example structure (abbreviated):
    ```json
    {
      "extractedCriteria": {
        "eignungskriterien": { ... },
        "zuschlagskriterien": [ ... ],
        "subunternehmerregelung": [ ... ],
        "formale_anforderungen": [ ... ]
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
- **filename.ext.meta.json** (next to documents):
  - Purpose: Stores metadata specific to individual documents.
  - Content: Includes fields like aussteller, beschreibung, metadaten (array).
  - Example:
    ```json
    {
      "aussteller": "Wiener Wohnen Hausbetreuung GmbH",
      "beschreibung": "Das Dokument wird im Titel und im Einleitungstext explizit als 'Leitfaden zum Angebot' bezeichnet und dient dazu, Bieter durch die Ausschreibung zu führen und beim Aufbau des Angebots zu unterstützen.",
      "metadaten": []
    }
    ```
- **.pdf2md_index.json** (hidden file in directories like project root or A/B):
  This file serves as an index for PDF to Markdown conversions within a directory. It tracks the parsing status and available parsers for each document. Its structure is as follows:

  ```json
  {
    "files": [
      {
        "name": "document_name.pdf",
        "size": 12345,  // Original file size in bytes
        "hash": "md5_hash",  // File content hash for integrity checking
        "parsers": {
          "status": "completed" | "pending" | "failed",
          "det": ["docling", "pdfplumber"],  // Available parsers for this file
          "default": "docling"  // Default parser to use
        },
        "meta": {  // Optional document metadata
          "kategorie": "Eignungsnachweise",  // Document category (e.g., Berufliche Zuverlässigkeit)
          "name": "Document display name"  // Human-readable document name
        }
      },
      // ... more file entries
    ],
    "directories": [],  // Currently unused
    "timestamp": 1234567890.123  // Last update timestamp
  }
  ```
  
  **Meta Fields Explanation**:
  - `size`: Original file size in bytes for reference
  - `hash`: MD5 hash of file content for integrity verification
  - `meta.kategorie`: Categorizes the document (e.g., "Berufliche Zuverlässigkeit", "Eignungsnachweise")
  - `meta.name`: Human-readable display name for the document
  - `timestamp`: Unix timestamp of last index update

  - `files`: An array of objects, each representing a document in the directory.
  - `name`: The name of the original document (e.g., `document_name.pdf`).
  - `parsers`: An object containing parsing-related metadata:
    - `status`: The current parsing status of the document (e.g., `completed`, `pending`, `failed`).
    - `det`: An array of strings indicating the parsers detected or used for the document (e.g., `docling`, `pdfplumber`).
    - `default`: A string specifying the default parser to be used for the document.
  - Purpose: Indexing for PDF-to-Markdown conversions to avoid redundant processing.
  - Content: Maps original files to their converted versions, including timestamps, processor used, and status (e.g., successful, failed).

These JSON files enable efficient data retrieval, integrity checks, and integration with AI analysis tools.

## WebDAV Path Construction

WebDAV paths are built from user-configured parameters in settings:

- Base URL (e.g., `https://webdav.example.com`)
- Path prefix (e.g., `/remote/disk`)
- Full path example: `https://webdav.example.com/remote/disk/2025-04 Lampen/A/2024_06001_AAB_EV.pdf`

This allows seamless remote access and synchronization.

## Best Practices

- Always place new projects at the root level.
- Use processing workers to generate `md/` content automatically.
- Update metadata JSON files via API endpoints for consistency.
- Archive completed projects to maintain a clean active workspace.

## Condensed Example File Structure

Below is a condensed example of the opinionated filesystem structure:

```
disk/
├── 2025-04 Lampen/                      # Project folder
│   ├── A/                               # Tender documents
│   │   ├── 2024_06001_AAB_EV.pdf        # Original tender document
│   │   ├── 2024_06001_Beilage_01.docx   # Original attachment
│   │   └── md/                          # Markdown conversions
│   │       ├── 2024_06001_AAB_EV.docling.md       # Converted via docling
│   │       ├── 2024_06001_AAB_EV.pdfplumber.md    # Converted via pdfplumber
│   │       └── 2024_06001_AAB_EV/                 # Extracted assets
│   │           ├── _page_0_Picture_5.jpeg         # Extracted image
│   │           └── 2024_06001_AAB_EV.marker.md    # Marker conversion
│   ├── B/                               # Bidder documents
│   │   ├── Lampion/                     # Specific bidder folder
│   │   │   ├── 1completed-austrian-document.pdf   # Original bidder document
│   │   │   └── md/                      # Markdown conversions
│   │   │       ├── 1completed-austrian-document.docling.md
│   │   │       └── 1completed-austrian-document/
│   │   │           └── 1completed-austrian-document.marker.md
│   │   └── archive/                     # Archived bidder folders
│   │       └── Lampion2/                # Archived version of bidder
│   ├── projekt.meta.json                # Project metadata
│   └── kriterien.meta.json              # Extracted criteria
├── A-TEST/                              # Another project
│   ├── A/
│   ├── B/
│   └── projekt.meta.json
└── archive/                             # Archived projects
    └── OldProject/                      # Archived project folder
```

This structure illustrates:

- Project folders at the root level
- Clear separation between tender (A/) and bidder (B/) documents
- Markdown conversion folders (md/) with processor-specific files
- Extracted assets in subdirectories
- Metadata files at the project level
- Archive directories for both bidders and completed projects

## Metadata File Specifications (Focused Overview)

This section consolidates and deepens the description of the three core JSON metadata artifacts referenced across tools (`pdf2md`, `strukt2meta`) and visible in the sample project tree (`.dir`).

### 1. projekt.meta.json (Project-Level Canonical Metadata)
Location: Project root (e.g., `2025-04 Lampen/projekt.meta.json`)
Purpose: Canonical high-level tender/project descriptor used for UI, search, enrichment context.
Lifecycle:
- Created after initial document ingestion or first metadata extraction run.
- Updated when AI extraction or manual curation adds / changes project facts.
- Read-only for downstream parsing steps (they should not overwrite core identity fields without explicit user action).

Minimal Field Set (recommended):
```
{
  "projektName": "Leuchten, Masten, Ausleger",          # Human readable project name
  "referenznummer": "AS 2024.06001",                   # Tender reference / internal ID
  "vergabestelle": "Wiener Wohnen Hausbetreuung GmbH", # Contracting authority
  "adresse": "Erdbergstraße 200, 1030 Wien",           # Authority address
  "sprache": "Deutsch",                                # Primary language
  "beschreibung": "...",                               # Short summary (<= 600 chars)
  "startDatum": "NONE",                                # If unknown use "NONE" or null
  "bieterabgabe": "2025-06-16",                        # Bid submission deadline
  "projektStart": "NONE",
  "endDatum": "NONE",
  "dokumentdatum": "2025-07-31",                       # Date of key base doc (AAB)
  "schlagworte": "comma,separated,keywords",
  "selectedParser": null,                               # Preferred parser id (optional)
  "metadaten": []                                       # Future structured enrichments
}
```
Best Practices:
- Keep immutable identity keys (`referenznummer`) stable; if changed, log history externally.
- Normalize dates to ISO `YYYY-MM-DD`.
- Consider adding a `version` and `updatedAt` field in future schema evolution.

### 2. kriterien.meta.json (Extracted Criteria & Compliance Model)
Location: Project root (optional; created when criteria extraction runs successfully).
Purpose: Central structured representation of award & suitability criteria for scoring, compliance checking, and bid guidance.
Typical Structure (abridged):
```
{
  "extractedCriteria": {
    "eignungskriterien": { ... },            # Suitability requirements (object or list)
    "zuschlagskriterien": [ { ... } ],        # Award criteria list with weights
    "subunternehmerregelung": [ ... ],       # Subcontracting clauses
    "formale_anforderungen": [ ... ]         # Formal submission rules
  },
  "aabFileName": "2024_06001_AAB_EV.pdf",    # Source anchor document
  "extractionMethod": "KRITERIEN_EXTRAKTION", # Extraction pipeline id
  "extractionTimestamp": "2025-07-31T14:09:10Z",
  "lastModified": "2025-07-31T14:09:10Z",
  "version": "1.0",
  "reviewStatus": { "aiReviewed": true, "humanReviewed": false }
}
```
Best Practices:
- Always persist `aabFileName` (traceability to governing source).
- Include weights/points inside each `zuschlagskriterien` entry where applicable.
- Introduce `normalizationVersion` if scoring normalization logic changes later.
- After human review, set `reviewStatus.humanReviewed=true` and optionally add `approver` + `reviewTimestamp`.

### 3. .pdf2md_index.json (Directory-Level Parse & Metadata Index)
Location: Any directory containing source documents (`A/`, bidder subfolders, etc.).
Purpose: Operational index for file discovery, parser coverage tracking, and document-level metadata attachment (lightweight enrichment layer).
Key Sections:
```
{
  "schema_version": 1,                 # (Planned field, may be absent in legacy files)
  "timestamp": 1732972365.123,         # Last write epoch
  "files": [
    {
      "name": "2024_06001_AAB_EV.pdf",
      "size": 123456,
      "hash": "<sha256|md5>",          # Integrity & change detection
      "parsers": {
        "status": "completed",        # Legacy aggregate status (optional)
        "det": ["docling", "pdfplumber"],
        "default": "docling"          # Preferred parser selection (optional)
      },
      "meta": {
        "kategorie": "Ausschreibungsunterlagen", # Domain category
        "name": "AAB EV"                         # Human-friendly label
      }
    }
  ],
  "directories": []
}
```
Modernization Direction (OFS Core):
- Introduce `parsers` map with per-parser objects: `{ "docling": {"ts": ..., "ok": true}}` while maintaining `parsers.det` for backward compatibility.
- Add optional `rel_path` to decouple from physical moves.
- Provide idempotent update semantics via `record_parse` API.

Integrity & Consistency:
- If file hash changes but size identical: treat as modified; re-parse may be required.
- Stale index detection: compare `timestamp` against file mtimes; schedule re-scan.
- Recovery: If JSON corrupt → back up corrupted file (`.bak`) and regenerate.

### Relationships & Flow
1. Raw documents enter `A/` or `B/<Bidder>/`.
2. Conversions populate `md/` and update `.pdf2md_index.json` (parser coverage).
3. Project-level synthesis produces / updates `projekt.meta.json`.
4. Criteria extraction pipeline outputs `kriterien.meta.json` referencing authoritative source doc(s) recorded in the index.
5. Downstream enrichment (categorization, AI metadata) augments `meta` blocks inside the index and/or adds structured objects to `projekt.meta.json`.

### Example Cross-Referencing (Using Tree)
- `2025-04 Lampen/A/2024_06001_AAB_EV.pdf` → entry in `A/.pdf2md_index.json` with parsers `[docling, pdfplumber, marker]`.
- Criteria extraction sets `aabFileName` = that file in `kriterien.meta.json`.
- `projekt.meta.json` `projektName` and `referenznummer` surface in UI search; `schlagworte` support tag-based retrieval.

### Validation Checklist (Recommended Before Deployment)
| Check | File | Condition |
|-------|------|-----------|
| Project identity present | projekt.meta.json | `projektName` & `referenznummer` non-empty |
| Core deadlines consistent | projekt.meta.json | `bieterabgabe` >= today or flagged archived |
| AAB reference resolvable | kriterien.meta.json | `aabFileName` exists in index `files` list |
| Parser coverage threshold | .pdf2md_index.json | Required minimum parser(s) executed |
| Categorization completeness | .pdf2md_index.json | All `meta.kategorie` populated (or queued) |

### Tooling Implications
- `pdf2md` updates index incrementally → no direct writes to project / criteria JSON.
- `strukt2meta` reads index to decide which markdown version to use and to inject metadata back.
- Future OFS Core centralizes JSON schema validation & graceful migrations.

### Future Enhancements (Planned)
- Add `projectId` GUID to `projekt.meta.json` & echo in index entries for join efficiency.
- Maintain `criteriaHash` in `kriterien.meta.json` to detect drift after document updates.
- Introduce `meta.provenance` per document listing parser + model + timestamp for each metadata field.

---
