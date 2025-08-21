# strukt2meta

`strukt2meta` is a compact Python CLI utility that generates structured JSON metadata from documents (typically markdown, PDFs, DOCX, etc.) using AI prompts. It is designed to integrate with Opinionated File Systems (OFS) and supports prompt-driven analysis, selective JSON injection, and batch workflows.

## Highlights

- Prompt-driven metadata generation (templates live in `./prompts`)
- OFS-compatible: reads and updates directory index files (`.ofs.index.json`, legacy `.pdf2md_index.json`)
- Automatic prompt selection for opinionated directory layouts (`/A/` → `adok`, `/B/` → `bdok`)
- New default injection behavior: always write a per-file sidecar containing the full generated metadata and selectively push a small set of fields into the index (see "Behavior notes" for details)
- Selective index fields are configurable (`index_meta_fields`) and can be set per-project or via environment
- Specialized extraction for German tender documents (`kriterien`)
- Integrates with `credgoo` (credentials) and `uniinfer` (AI providers)

## Installation

```/dev/null/install.sh#L1-2
pip install -r requirements.txt
```

Python 3.8+ is recommended. Ensure AI credentials are available (handled via `credgoo`).

## Quick examples

Generate metadata from a single source:
```/dev/null/generate.example#L1-2
strukt2meta generate --i input.md --p zusammenfassung --o metadata.json
```

Process uncategorized items (automatic `adok`/`bdok` selection):
```/dev/null/unlist.example#L1-2
strukt2meta unlist 5 ./un_items.json -d ./data --prompt metadata_extraction -v
```

Extract qualification criteria from a tender document:
```/dev/null/kriterien.example#L1-2
strukt2meta kriterien -p ./prompts/kriterien.md -f tender.pdf -o criteria.json
```

Inject pre-made metadata into a target JSON (dry run available):
```/dev/null/inject.example#L1-2
strukt2meta inject --params injection_params.json --dry-run
```

## Commands (concise)

- `generate` — Create metadata from a single source file and write JSON.
  - Key options: `--i/--inpath`, `--p/--prompt`, `--o/--outfile`, `--j/--json-cleanup`, `-v/--verbose`.

- `unlist` — Batch-process a list of uncategorized files (JSON with `un_items`).
  - Auto-selects `adok`/`bdok` by path; can update the OFS index and optionally inject results elsewhere.

- `kriterien` — Extract structured qualification criteria from tender documents.
  - Supports `--insert` to merge results into an existing JSON key.

- `inject` — Insert or update metadata in a target JSON using a params file.
  - Supports dry-run and verbose modes.

- `discover` — Find and rank candidate source files in a directory (parser ranking).
  - Useful before running `analyze` or `dirmeta`.

- `analyze` — List candidates or analyze a single file with AI (adds `meta_status`).
  - Listing mode prints candidates and their best markdown variants; file mode runs the prompt.

- `dirmeta` — Generate & inject metadata for all supported files in a directory.
  - Skips existing metadata by default; `--overwrite` to force.

- `clearmeta` — Remove specific or all top-level fields from a JSON index (supports dry-run).

- `batch` — Deprecated. Use `dirmeta`.

## Behavior notes

- Automatic prompt selection:
  - Files under a path segment `/A/` → `adok`
  - Files under `/B/` → `bdok`
  - Otherwise use the provided `--prompt` fallback

- Filters out common image formats from text-analysis flows.

- AI provenance:
  - The `Autor` (author) field is populated with trace info: `KI-generiert {provider}@{model}@{prompt}@{parser} {date}`.

- JSON cleanup:
  - The tool can attempt to repair malformed JSON produced by the AI (`--json-cleanup` / `--j`), and many calls enable JSON cleanup by default for injection flows.

- New default injection behavior (sidecar + selective index push):
  - By default the tool now writes a sidecar file next to each source file containing the full generated metadata. Naming convention:
    - For `INFO.pdf` the sidecar is `INFO.pdf.meta.json`.
  - The full metadata is preserved in the sidecar; the global index (`.ofs.index.json` or configured index file) is only updated with a small subset of fields.
  - The fields pushed into the index are taken from `index_meta_fields` (order of precedence):
    1. `index_meta_fields` given in a JSONInjector params file (for batch flows).
    2. `config.json` in the file's directory (or repo root) with key `"index_meta_fields": ["field1","field2"]`.
    3. Environment variable `STRUKT2META_INDEX_FIELDS="field1,field2"` (helper override).
    4. Built-in default: `["name", "kategorie", "begründung"]`.
  - The index is only written/updated if at least one of the configured `index_meta_fields` exists and is non-empty in the generated metadata. If none of the configured fields are present, the sidecar is still written but the index stays unchanged.
  - Index files are updated directly without creating backup files.

- Rationale:
  - Sidecars store the authoritative, full metadata produced by the AI and avoid data loss when the index schema is intentionally minimal.
  - Selective index pushing keeps the index small and focused on the most relevant fields while preserving complete metadata per-file for deeper inspection or re-processing.

## Output examples

- Sidecar (full metadata)
  - After a successful run the tool writes a sidecar file next to the source file containing the full metadata produced by the AI. Example:
    - `INFO.pdf.meta.json` (contains the complete AI-generated JSON, typically including `meta` sub-keys, extracted content, and any auxiliary fields).

- Index (selective fields)
  - The global index (e.g. `.ofs.index.json`) will be updated only with configured, important fields (default: `["name", "kategorie", "begründung"]`). Example index entry after an update:
    ```json
    {
      "name": "INFO.pdf",
      "meta": {
        "name": "INFO.pdf",
        "kategorie": "Lieferung",
        "begründung": "Erfüllt die Mindestanforderungen"
      }
    }
    ```
  - If the AI result did not contain any of the configured index fields, the index is left unchanged and the full result remains available in the sidecar.

- `kriterien` output
  - The `kriterien` command still produces a nested, structured JSON of criteria (e.g. `eignungskriterien`, `befugnis`, `technische_leistungsfaehigkeit`) and that full result will be written to the sidecar; selective fields from it can be pushed to the index depending on configuration.

## Dependencies

- See `requirements.txt` (includes `uniinfer`, `credgoo`)
- Valid AI credentials are required (managed via `credgoo`)

## Programmatic API Usage

In addition to the CLI you can import `strukt2meta` and call high‑level functions directly (since version 0.1.1).

### Quick Start

```python
from strukt2meta import generate_metadata_from_file, dirmeta_process

# Generate metadata for a single markdown file
meta = generate_metadata_from_file("sample_document.md", "zusammenfassung", json_cleanup=True)
print(meta)

# Process an entire directory (writes sidecars + selective index updates)
summary = dirmeta_process("./mydocs", prompt="metadata_extraction")
print(summary)
```

### Available Functions

- `generate_metadata_from_text(prompt_name, text, json_cleanup=False, verbose=False)` → dict
- `generate_metadata_from_file(file_path, prompt_name, ...)` → dict
- `discover_files(directory)` → list[FileMapping]
- `analyze_file(directory, source_filename, prompt='metadata_extraction', json_file=None)` → dict with metadata & status
- `dirmeta_process(directory, prompt, json_file=None, overwrite=False)` → summary dict
- `inject_with_params(params_file)` → result dict (advanced schema-driven flow)
- `inject_metadata(source_filename, metadata, json_index_path, base_directory=None)` → bool
- `Strukt2Meta` facade class offering object-oriented convenience wrappers.

All functions raise standard exceptions (e.g. `FileNotFoundError`) on fatal issues instead of exiting the process so you can handle errors gracefully.

### Facade Example

```python
from strukt2meta import Strukt2Meta

s2m = Strukt2Meta(verbose=True)
result = s2m.generate_from_file("sample_document.md", "zusammenfassung", json_cleanup=True)
print(result["meta"])  # or any keys returned by the prompt

summary = s2m.dirmeta("./project_docs", prompt="metadata_extraction", overwrite=False)
print(summary)
```

Sidecar + selective index behavior is preserved exactly like the CLI: each processed file gets `<filename>.meta.json` with full metadata; only configured `index_meta_fields` are pushed to the index file.

## Developer Guide

### OFS Integration and Metadata Injection

The `ofs` command integrates with Opinionated File Systems (OFS) to automatically process documents and inject metadata into structured JSON index files.

#### Metadata Injection Locations

**Project Documents (A/ directory):**
- File: `.ofs.index.json`
- Location: `{project_path}/A/.ofs.index.json`
- Prompt: `adok` (project document analysis)

**Bidder Documents:**
- File: `.ofs.index.json`
- Location: `{bidder_path}/.ofs.index.json`
- Prompt: `bdok` (bidder document analysis)

#### JSON Index Structure

The metadata is injected into JSON index files with the following structure:

```json
{
  "files": [
    {
      "name": "document.pdf",
      "meta": {
        "kategorie": "Beilage",
        "aussteller": "Company Name",
        "name": "Document Title",
        "begründung": "Analysis reasoning..."
      }
    }
  ],
  "created": "2024-01-15T10:30:00",
  "last_updated": "2024-01-15T10:35:00"
}
```

#### OFS Command Usage

```bash
# Process entire project
strukt2meta ofs PROJECT_NAME

# Process specific bidder
strukt2meta ofs PROJECT_NAME@BIDDER_NAME

# Process specific project file
strukt2meta ofs "PROJECT_NAME@FILENAME"

# Process specific bidder file
strukt2meta ofs "PROJECT_NAME@BIDDER_NAME@FILENAME"
```

#### Injection Process

1. **Document Reading**: Uses OFS `read_doc()` to access pre-parsed markdown content
2. **Prompt Selection**: Automatically selects `adok` for project docs or `bdok` for bidder docs
3. **AI Generation**: Generates structured metadata using the selected prompt
4. **Index Update**: Merges metadata into the appropriate `.ofs.index.json` file
5. **Preservation**: Maintains existing metadata fields while adding new ones

The injection preserves the original document structure while adding searchable, structured metadata that can be used by other OFS-compatible tools.

## Project Status

**Current Version:** 0.0.6

**Core Features Implemented:**
- ✅ Prompt-driven metadata generation with template system
- ✅ AI integration via uniinfer with multiple provider support
- ✅ JSON schema validation and cleanup
- ✅ Intelligent file discovery with parser ranking
- ✅ Sidecar metadata files with selective index injection
- ✅ OFS (Opinionated File System) integration
- ✅ Specialized German tender document processing (`kriterien`)
- ✅ Comprehensive CLI with 10 commands
- ✅ Batch processing with automatic markdown selection
- ✅ Configuration-driven architecture

**Production Ready:** Successfully deployed and tested with real-world German procurement documents (Lampen project with 22+ documents).

## Contributing

- Add or refine prompts in `./prompts/`
- Improve parser ranking/config via `discover` config options
- Open issues or PRs for bugs, new extractors, or provider integrations

For detailed command usage, run:
```/dev/null/help.example#L1-1
strukt2meta --help
```
