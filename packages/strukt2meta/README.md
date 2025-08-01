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

`strukt2meta` can be run from the command line. Here's how to use it:

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
- [ ] JSON output schema definition
- [ ] API calling with `uniinfer`
- [ ] JSON cleanify routine for AI-generated JSON