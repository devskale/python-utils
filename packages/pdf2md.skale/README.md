# pdf2md-skale: Elegant PDF to Markdown Converter

`pdf2md-skale` is a versatile Python package designed to convert PDF files into Markdown format. It offers a range of extraction methods, including text-based and OCR-based approaches, to ensure accurate and comprehensive conversion. This tool is particularly useful for extracting content from PDFs for note-taking, content repurposing, or data analysis.

## Features

- **Multiple Extraction Methods:** Supports various PDF text extraction libraries:
  - `pdfplumber`: For extracting text from well-structured PDFs.
  - `PyPDF2`: Another robust library for text extraction.
  - `PyMuPDF`: A fast and feature-rich PDF processing library.
  - `LlamaParse`: Leverages the Llama Cloud API for advanced parsing and Markdown output.
  - `OCR (Tesseract)`: Optical Character Recognition for image-based PDFs.
  - `EasyOCR`: Another OCR engine, offering multilingual support.
  - `Docling`: A new approach to extract text from pdfs.
  - `Marker`: Uses marker extraction for enhanced text processing (creates dedicated subdirectory structure for each PDF).
- **Recursive Processing:** Option to process directories recursively with `--recursive` flag.
- **Dry Run Mode:** Preview file counts without conversion using `--dry` flag.
- **Markdown Output:** Generates clean Markdown files, preserving text formatting.
- **Metadata Inclusion:** Adds a YAML header to each Markdown file with:
  - Title (derived from the PDF filename).
  - Creation date.
  - Number of pages.
  - Word count.
  - Character count.
  - Extractor used.
- **Command-Line Interface:** Easy to use with command-line arguments for input/output directories, overwriting files, and selecting extraction methods.
- **OCR Support:** Handles image-based PDFs using OCR, with language selection.
- **Error Handling:** Gracefully handles errors during conversion and provides informative messages.
- **Environment Variable Support:** Uses `.env` file for API keys (e.g., `LLAMA_CLOUD_API_KEY`).
- **Multiple Parsers:** You can select multiple parsers to use.
- **System Architecture:** Updated architecture supports modular extractors and processors.
- **Indexing System:** Comprehensive file tracking with hash-based change detection and parser status tracking.

## Prerequisites

- Python 3.8+
- Required Python packages (install using `pip`):

  ```bash
  pip install pdfplumber PyPDF2 pymupdf python-dotenv llama-parse llama-index tesseract docling easyocr marker
  ```

  - **Tesseract OCR:** If you plan to use OCR, you'll need to install Tesseract OCR separately.
    - **macOS:** `brew install tesseract`
    - **Ubuntu/Debian:** `sudo apt-get install tesseract-ocr`
    - **Windows:** Download from Tesseract OCR website and add it to your system's PATH.
  - **EasyOCR**: If you plan to use EasyOCR, you need to install it separately.
    - `pip install easyocr`
  - **Docling**: If you plan to use Docling, you need to install it separately.
    - `pip install docling`
  - **Marker**: If you plan to use Marker extraction, you need to install it separately.
    - `pip install marker`

- **LLAMA_CLOUD_API_KEY (Optional):** If you want to use the `llamaparse` extractor, you need to set the `LLAMA_CLOUD_API_KEY` environment variable. You can do this either by:

  1. Creating a `.env` file in the same directory as the script and adding:

     ```
     LLAMA_CLOUD_API_KEY=your_api_key_here
     ```

  2. Using the credgoo library (recommended, see [documentation](https://github.com/devskale/python-utils/blob/master/README.md)):
     ```bash
     pip install git+https://github.com/devskale/python-utils.git#subdirectory=packages/credgoo
     ```
     Then in your code:
     ```python
     from credgoo import get_credential
     llama_api_key = get_credential('llamacloud')
     ```

## Usage

1.  **Basic Conversion (pdfplumber):**

    ```bash
    pdf2md <input_directory> <output_directory>
    ```

    - `<input_directory>`: The directory containing the PDF files you want to convert.
    - `<output_directory>`: The directory where the Markdown files will be saved.
    - If you don't specify the directories, it will use the default directories:
      - input: `/Users/johannwaldherr/code/ww/ww_private/vDaten/work`
      - output: `/Users/johannwaldherr/code/ww/ww_private/vDaten/work/md`

2.  **Overwrite Existing Files:**

    ```bash
    pdf2md <input_directory> --overwrite
    ```

    - The `--overwrite` flag will force the script to overwrite existing Markdown files.

3.  **Using OCR:**

    ```bash
    pdf2md <input_directory> --ocr
    ```

    - The `--ocr` flag enables OCR for text extraction.

4.  **OCR Language:**

    ```bash
    pdf2md <input_directory> --ocr --ocr-lang deu
    ```

    - The `--ocr-lang` flag specifies the language for OCR (e.g., `deu` for German, `eng` for English). Default is `deu`.

5.  **Selecting Parsers:**

    ```bash
    pdf2md <input_directory> --parsers pdfplumber llamaparse ocr
    ```

    - The `--parsers` flag allows you to specify which parsers to use. You can list multiple parsers separated by spaces.
    - Available parsers: `pdfplumber`, `pypdf2`, `pymupdf`, `llamaparse`, `ocr`, `easyocr`, `docling`, `marker`.
    - Note: `marker` extractor only works with PDF files and creates a dedicated subdirectory for each PDF.

6.  **Using multiple parsers**
    ```bash
    pdf2md <input_directory> --parsers pdfplumber pymupdf
    ```
    - This will create two markdown files for each pdf, one with the pdfplumber parser and one with the pymupdf parser.

## Indexing System

The pdf2md tool includes a sophisticated indexing system that tracks:

- File metadata (name, size, hash)
- Parser status for each file
- Directory structure changes

The index helps with:

1. **Incremental Updates:** Only processes changed files by comparing hashes
2. **Parser Status Tracking:** Knows which parsers have already processed each file
3. **Change Detection:** Identifies added, removed or modified files
4. **Directory Monitoring:** Tracks nested directory structures

### Current Index Features

- **Index Creation:** Generates `.pdf2md_index.json` files in directories to track file and directory metadata.
- **Index Updates:** Updates existing index files if they are older than a specified age (default: 30 seconds, configurable with `--index-age`).
- **Index Clearing:** Removes all index files from specified directories.
- **Index Stats:** Provides detailed statistics about indexed files, including document counts, parser usage, and categories.
- **Test Mode:** Allows testing index updates without making changes.
- **Parsing Status:** Displays files that have not been parsed by any parser or a specific parser.

Index files (`.pdf2md_index.json`) are created in each processed directory. You can manage indexes using these CLI options:

```bash
# Create fresh indexes
pdf2md --index create

# Update existing indexes
pdf2md --index update --index-age 60  # Update indexes older than 60 seconds

# Clear all indexes
pdf2md --index clear

# Print index stats
pdf2md --index stats

# Show parsing status
pdf2md --status all  # Show files not parsed by any parser
pdf2md --status pdfplumber  # Show files not parsed by 'pdfplumber'
```

## Example

```bash
# Basic conversion with default parser
pdf2md my_pdfs

# Recursive processing with multiple parsers
pdf2md my_pdfs --recursive --parsers pdfplumber marker --overwrite

# Dry run to preview file counts
pdf2md my_pdfs --dry --recursive
```

## Additional CLI Example

```bash
pdf2md /Users/johannwaldherr/code/ww/ww_private/vDaten/work \
       /Users/johannwaldherr/code/ww/ww_private/vDaten/work/md \
       --ocr --ocr-lang eng
```

## Python Library Usage

```python
from pdf2md.converter import PDFtoMarkdown

converter = PDFtoMarkdown(['ocr'])
converter.convert('example.pdf', 'output_dir', 'example.md', 'ocr', overwrite=True)
```

# Status

[x] Basic functionality
[x] Recursive processing
[x] Dry run mode
[ ] OlmoOCR
[ ] Process Images
[ ] API Queuing System
