# strukt2meta

`strukt2meta` is a compact Python CLI utility that generates structured JSON metadata from documents (typically markdown, PDFs, DOCX, etc.) using AI prompts. It is designed to integrate with Opinionated File Systems (OFS) and supports prompt-driven analysis, selective JSON injection, and batch workflows.

## Highlights

- Prompt-driven metadata generation (templates live in `./prompts`)
- OFS-compatible: reads and updates directory index files (`.ofs.index.json`, legacy `.pdf2md_index.json`)
- Automatic prompt selection for opinionated directory layouts (`/A/` → `adok`, `/B/` → `bdok`)
- JSON "inject" / "insert" modes to avoid overwriting unrelated fields
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
- `Autor` field is populated with trace info: `KI-generiert {provider}@{model}@{prompt}@{parser} {date}`.
- Optional JSON clean-up attempts to fix AI-generated JSON structure before writing.

## Output examples

Typical generated JSON contains metadata fields such as `title`, `summary`, `tags`, and traceable `author` info. For `kriterien`, a structured schema with categories (e.g. `eignungskriterien`) is produced.

## Dependencies

- See `requirements.txt` (includes `uniinfer`, `credgoo`)
- Valid AI credentials are required (managed via `credgoo`)

## Project status

Core features implemented: prompts handling, AI integration, JSON schema & cleanup, injection/insert modes, `unlist` batch flow, `kriterien` extraction, CLI. Ongoing: refinements, additional prompt templates, more parser adapters.

## Contributing

- Add or refine prompts in `./prompts/`
- Improve parser ranking/config via `discover` config options
- Open issues or PRs for bugs, new extractors, or provider integrations

For detailed command usage, run:
```/dev/null/help.example#L1-1
strukt2meta --help
```
