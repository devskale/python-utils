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
- **Indexing System:** A robust indexing system that tracks file metadata, parser status, and directory changes. It enables:
  - Incremental updates by processing only changed files.
  - Parser status tracking to identify which files have been processed by specific parsers.
  - Change detection for added, removed, or modified files.
  - Directory monitoring for nested structures.

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

## New Feature: Single File Input Support

`pdf2md-skale` now supports processing single files in addition to directories. This enhancement provides greater flexibility and efficiency for users who want to process individual files without scanning entire directories.

### Key Features of Single File Support

- **File vs Directory Detection:** Automatically detects whether the input path is a file or a directory.
- **Supported File Types:** Single file processing supports `.pdf`, `.docx`, `.xlsx`, and `.pptx` file types.
- **Parser Compatibility Check:** Ensures the specified parsers are compatible with the file type.
- **Error Handling:** Provides clear error messages for unsupported file types or non-existent paths.
- **Index Operations:** All index-related commands (`create`, `update`, `clear`, `stats`, `un`) work seamlessly with single files by using the parent directory for index management.
- **Dry Run Mode:** Displays file details and compatible parsers for single files without performing conversion.

### Usage Examples

1. **Process a Single File:**

    ```bash
    pdf2md /path/to/document.pdf --parsers pdfplumber
    ```

2. **Dry Run for a Single File:**

    ```bash
    pdf2md /path/to/document.pdf --dry
    ```

3. **Index Operations for Single Files:**

    ```bash
    pdf2md /path/to/document.pdf --index update
    ```

4. **Check Parsing Status for Single Files:**

    ```bash
    pdf2md /path/to/document.pdf --status
    ```

### Benefits

- **Flexibility:** Process individual files without scanning directories.
- **Efficiency:** Focus on specific files for faster processing.
- **Consistency:** Single file processing integrates seamlessly with existing features like indexing and status checks.

This update ensures that `pdf2md-skale` remains a versatile and user-friendly tool for all your PDF-to-Markdown conversion needs.

## Indexing System

The indexing system is a core feature of `pdf2md-skale`, designed to streamline and optimize the conversion process. It creates and manages `.pdf2md_index.json` files in each directory, which store metadata about files and directories.

### Key Benefits

1. **Incremental Updates:** 
   - Tracks file changes using hashes and metadata.
   - Processes only files that have been added, modified, or removed since the last index update.

2. **Parser Status Tracking:**
   - Records which parsers have processed each file.
   - Helps identify unparsed files or files that need reprocessing with specific parsers.

3. **Change Detection:**
   - Detects added, removed, or modified files and directories.
   - Ensures accurate and up-to-date indexing.

4. **Directory Monitoring:**
   - Tracks nested directory structures.
   - Provides detailed statistics about indexed files and directories.

### Index Management Commands

You can manage indexes using the following CLI options:

- **Create Indexes:**
  ```bash
  pdf2md --index create
  ```
  Creates fresh `.pdf2md_index.json` files in the specified directory and its subdirectories (if `--recursive` is used).

- **Update Indexes:**
  ```bash
  pdf2md --index update --index-age 60
  ```
  Updates existing `.pdf2md_index.json` files if they are older than 60 seconds.

- **Clear Indexes:**
  ```bash
  pdf2md --index clear
  ```
  Removes all `.pdf2md_index.json` files from the specified directory.

- **Print Index Stats:**
  ```bash
  pdf2md --index stats
  ```
  Displays detailed statistics about indexed files, including document counts, parser usage, and categories.

- **Show Parsing Status:**
  ```bash
  pdf2md --status all
  ```
  Lists files that have not been parsed by any parser.

  ```bash
  pdf2md --status pdfplumber
  ```
  Lists files that have not been parsed by the `pdfplumber` parser.

### Example Workflow

1. **Create Indexes:**
   ```bash
   pdf2md --index create /path/to/directory
   ```
   Generates `.pdf2md_index.json` files in `/path/to/directory` and its subdirectories.

2. **Update Indexes:**
   ```bash
   pdf2md --index update /path/to/directory --index-age 30
   ```
   Updates `.pdf2md_index.json` files if they are older than 30 seconds.

3. **Clear Indexes:**
   ```bash
   pdf2md --index clear /path/to/directory
   ```
   Deletes all `.pdf2md_index.json` files in the specified directory.

4. **Print Index Stats:**
   ```bash
   pdf2md --index stats /path/to/directory
   ```
   Displays statistics about indexed files and directories.

5. **Check Parsing Status:**
   ```bash
   pdf2md --status all /path/to/directory
   ```
   Lists files that have not been parsed by any parser.

### Technical Details

- **Index File Format:** 
  - `.pdf2md_index.json` files store metadata about files and directories, including:
    - File name, size, and hash.
    - Parsers used and their status.
    - Metadata such as categories.

- **Hash-Based Tracking:** 
  - Uses MD5 hashes to detect file changes.
  - Ensures efficient and accurate indexing.

- **Parser Hierarchy:** 
  - Prioritizes parsers based on a predefined hierarchy (e.g., `docling`, `marker`, `llamaparse`, `pdfplumber`).

- **Test Mode:** 
  - Allows testing index creation or updates without making changes.

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
