# strukt2meta

`strukt2meta` is a Python utility designed to generate metadata from structured data or images using AI. It can analyze various inputs, including markdown files, and convert them into structured metadata based on predefined prompts. This metadata can then be injected into JSON files, particularly within an Opinionated File System (OFS) structure.

## Features

- **OFS Compatibility**: Works seamlessly with Opinionated File Systems (OFS).
- **Markdown Analysis**: Analyzes markdown content and converts it into metadata using AI prompts.
- **Recursive Processing**: Capable of processing OFS files, directories, and entire file trees recursively.
- **Strukt Context Retrieval**: Retrieves file paths as "strukt context" for AI processing.
- **Prompt-Driven Metadata Generation**: Accepts various prompts (e.g., from templates) to guide the AI model in generating relevant metadata.
- **AI Model Integration**: Queries AI models with the provided context and prompt.
- **JSON Output**: Typically returns AI-generated responses in JSON format.
- **JSON Injection**: Injects the generated JSON metadata into specified JSON files.
- **Criteria Extraction**: Automated extraction of qualification criteria from German tender documents with structured JSON output.
- **Insert Mode**: Targeted updates of specific JSON sections without overwriting entire files.

## Architecture

`strukt2meta` leverages the following libraries for its core functionalities:

- `credgoo`: Used for securely retrieving API keys.
- `uniinfer`: Provides access to various AI models from different providers, configured via a central configuration file.

## Installation

To set up `strukt2meta`, ensure you have Python installed. You can install the necessary dependencies using `pip`:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Generate metadata from a markdown file
python -m strukt2meta.main generate --i input.md --p zusammenfassung --o output.json

# Inject metadata into existing JSON files
python -m strukt2meta.main inject --params injection_params.json --verbose

# Process uncategorized files with simplified output
strukt2meta unlist 5 un_items.json --prompt metadata_extraction --verbose

# Process files from specific directory
strukt2meta unlist 10 .disk2/un_items.json -d .disk2
```

### Unlist Command

The `unlist` command processes uncategorized files and generates metadata with simplified output:

```bash
strukt2meta unlist <num> <json_file> [options]
```

**Parameters:**
- `num`: Number of files to process
- `json_file`: JSON file containing `un_items` array with file paths

**Options:**
- `-p, --prompt PROMPT`: Specify prompt name (default: metadata_extraction)
- `-d, --directory DIRECTORY`: Base directory for file paths
- `-t, --target-json TARGET_JSON`: Target JSON file for metadata
- `--verbose`: Enable verbose output

**Output Format:**
```
📄 rasenmaeher/B/rasenbieter1/Gesamtpdf-24-11-2023-12-19-00.pdf (sourcefile)
     bdok @ (content extracted directly)
     ok (json inserted)
```

**Automatic Prompt Selection:**
- Files in `/A/` directories use `adok` prompt
- Files in `/B/` directories use `bdok` prompt
- Other files use the specified `--prompt` parameter

`strukt2meta` provides multiple commands for different use cases:

### Commands

#### Generate Command
Generate metadata from a single source file:

```bash
python -m strukt2meta.main generate --inpath <input_file.md> --prompt <prompt_name> --outfile <output_file.json> [--verbose]
```

#### Unlist Command
Process uncategorized files from a JSON list for categorization:

```bash
python -m strukt2meta.main unlist <NUM> <json_file> [options]
```

**Arguments:**
- `NUM`: Number of files to process from the uncategorized list
- `json_file`: Path to the JSON file containing un_items array (e.g., un_items.json)

**Options:**
- `-p, --prompt`: Name of the prompt to use for categorization (default: metadata_extraction)
- `-d, --directory`: Base directory where the files are located
- `-t, --target-json`: Target JSON file to inject generated metadata into
- `--dry-run`: Show what files would be processed without actually processing them
- `--json-cleanup`: Enable auto-repair for AI-generated JSON output
- `-v, --verbose`: Enable verbose output for detailed logging

**Example:**
```bash
# Process 5 files from un_items.json for categorization
python -m strukt2meta.main unlist 5 ./un_items.json --prompt metadata_extraction --verbose

# Dry run to see what would be processed
python -m strukt2meta.main unlist 10 ./un_items.json --dry-run
```

The unlist command features:
- **Automatic Prompt Selection**: Uses opinionated file structure to select prompts:
  - Files in `/A/` directories automatically use the `adok` prompt
  - Files in `/B/` directories automatically use the `bdok` prompt
  - Other files use the specified `--prompt` parameter (fallback)
- **Automatic Index Update**: Automatically updates the `.pdf2md_index.json` file in each file's directory with generated metadata
- **Parser Type Detection**: Automatically detects and includes the parser type used for content extraction in the "Autor" field
- **AI Traceability**: Generates comprehensive "Autor" field with format: `"KI-generiert {provider}@{model}@{prompt}@{parser} {date}"`
- Filters out image files (png, jpg, jpeg, gif, bmp, tiff, svg, webp)
- Processes only files marked as `uncategorized: true`
- Extracts content from various file types for AI analysis
- Generates categorization metadata using the specified prompt
- Optional metadata injection into additional target JSON files

#### Kriterien Command
Extract qualification criteria from German tender documents:

```bash
python -m strukt2meta kriterien -p <prompt_file> -f <tender_document> -o <output.json> [options]
```

**Arguments:**
- `-p, --prompt`: Path to the prompt file (e.g., `./prompts/kriterien.md`)
- `-f, --file`: Path to the tender document file (PDF, DOCX, MD, etc.)
- `-o, --output`: Path to the output JSON file where criteria will be saved

**Options:**
- `-i, --insert`: Insert key for partial JSON updates (e.g., `eignungskriterien`)
- `-v, --verbose`: Enable verbose output for detailed processing information

**Examples:**
```bash
# Extract criteria from tender document
python -m strukt2meta kriterien -p ./prompts/kriterien.md -f ./tender_document.pdf -o ./criteria.json

# Update only specific section of existing JSON
python -m strukt2meta kriterien -p ./prompts/kriterien.md -f ./tender_document.pdf -o ./existing_criteria.json -i eignungskriterien

# Enable verbose logging
python -m strukt2meta kriterien -p ./prompts/kriterien.md -f ./tender_document.pdf -o ./criteria.json -v
```

**Features:**
- **Automated Criteria Extraction**: Identifies and structures qualification criteria from German tender documents
- **Structured JSON Output**: Generates consistent JSON format with categories like `eignungskriterien`, `befugnis`, etc.
- **Insert Mode**: Allows targeted updates of specific JSON sections without overwriting entire files
- **Visual Feedback**: Shows spinner animation during AI processing
- **Error Handling**: Comprehensive error handling with detailed logging
- **Statistics**: Reports number of extracted criteria and file size information

**Output Format:**
The kriterien command generates structured JSON with the following format:
```json
{
    "eignungskriterien": {
        "befugnis": [
            {
                "kriterium": "Description of qualification criterion",
                "nachweise": [
                    {
                        "typ": "PFLICHT|OPTIONAL",
                        "dokument": "Required document name",
                        "gueltigkeit": "Validity period if specified",
                        "hinweis": "Additional notes"
                    }
                ]
            }
        ],
        "berufliche_zuverlaessigkeit": [...],
        "technische_leistungsfaehigkeit": [...]
    }
}
```

### Legacy Usage (Generate Command)

For backward compatibility, you can still use the original syntax:

```bash
python -m strukt2meta.main --inpath <input_file.md> --prompt <prompt_name> --outfile <output_file.json> [--verbose]
```

### Arguments:

- `--i` or `--inpath`: Path to the input markdown "strukt" file. (default: `./default_input.md`)
- `--p` or `--prompt`: Name of the prompt file (without the `.md` extension) located in the `./prompts` directory. (default: `zusammenfassung`)
- `--o` or `--outfile`: Path to the output JSON file where the generated metadata will be saved. **This argument is required.**
- `-v` or `--verbose`: Enable verbose mode to stream the API call response.

### Example:

To process `my_document.md` using the `adok` prompt and save the output to `metadata.json`:

```bash
python -m strukt2meta.main --inpath ./my_document.md --prompt adok --outfile ./metadata.json
```

## Project Status

- [x] Basic package structure setup
- [x] `uniinfer` and `credgoo` installation
- [x] Configuration for AI provider, model, and tokens
- [x] Prompts file handling
- [x] JSON output schema definition
- [x] API calling with `uniinfer`
- [x] JSON cleanify routine for AI-generated JSON
- [x] JSON injection functionality
- [x] Unlist command for batch processing
- [x] Kriterien extraction for tender documents
- [x] Insert mode for targeted JSON updates
- [x] Visual feedback and error handling
- [x] Comprehensive CLI interface