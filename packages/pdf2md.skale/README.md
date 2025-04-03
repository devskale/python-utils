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
- **Docling Support**: Uses the docling library to extract text from pdfs.
- **Marker Support**: Uses marker extraction for enhanced text processing.
- **Environment Variable Support:** Uses `.env` file for API keys (e.g., `LLAMA_CLOUD_API_KEY`).
- **Multiple Parsers**: You can select multiple parsers to use.
- **System Architecture**: Updated architecture supports modular extractors and processors.

## Prerequisites

- Python 3.8+
- Required Python packages (install using `pip`):

  ```bash
  pip install pdfplumber PyPDF2 pymupdf python-dotenv llama-parse llama-index tesseract docling easyocr
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

- **LLAMA_CLOUD_API_KEY (Optional):** If you want to use the `llamaparse` extractor, you need to set the `LLAMA_CLOUD_API_KEY` environment variable. You can do this by creating a `.env` file in the same directory as the script and adding the line:

  ```
  LLAMA_CLOUD_API_KEY=your_api_key_here
  ```

## Usage

1.  **Basic Conversion (pdfplumber):**

    ```bash
    pdf2md-elegant <input_directory> <output_directory>
    ```

    - `<input_directory>`: The directory containing the PDF files you want to convert.
    - `<output_directory>`: The directory where the Markdown files will be saved.
    - If you don't specify the directories, it will use the default directories:
      - input: `/Users/johannwaldherr/code/ww/ww_private/vDaten/work`
      - output: `/Users/johannwaldherr/code/ww/ww_private/vDaten/work/md`

2.  **Overwrite Existing Files:**

    ```bash
    pdf2md-elegant <input_directory> --overwrite
    ```

    - The `--overwrite` flag will force the script to overwrite existing Markdown files.

3.  **Using OCR:**

    ```bash
    pdf2md-elegant <input_directory>  --ocr
    ```

    - The `--ocr` flag enables OCR for text extraction.

4.  **OCR Language:**

    ```bash
    pdf2md-elegant <input_directory> --ocr --ocr-lang deu
    ```

    - The `--ocr-lang` flag specifies the language for OCR (e.g., `deu` for German, `eng` for English). Default is `deu`.

5.  **Selecting Parsers:**

    ```bash
    pdf2md-elegant <input_directory> --parsers pdfplumber llamaparse ocr
    ```

    - The `--parsers` flag allows you to specify which parsers to use. You can list multiple parsers separated by spaces.
    - Available parsers: `pdfplumber`, `pypdf2`, `pymupdf`, `llamaparse`, `ocr`, `easyocr`, `docling`, `marker`.

6.  **Using multiple parsers**
    ```bash
    pdf2md-elegant <input_directory> --parsers pdfplumber pymupdf
    ```
    - This will create two markdown files for each pdf, one with the pdfplumber parser and one with the pymupdf parser.

## Example

```bash
pdf2md my_pdfs my_markdowns --overwrite --ocr --ocr-lang deu --parsers pdfplumber llamaparse easyocr
```
