# pdf2md-skale: Elegant PDF to Markdown Converter

`pdf2md-skale` is a comprehensive Python package designed to convert PDF files and Office documents into Markdown format. It offers multiple extraction methods, intelligent indexing, and robust directory filtering to ensure accurate and efficient document processing.

**pdf2md-skale adheres to the [OFS (Opinionated Filesystem) specification v1.0](https://github.com/devskale/python-utils/tree/master/packages/ofs)**, ensuring consistent directory structure and metadata handling for tender documentation workflows.

## Key Features

### 🔧 **Multiple Extraction Methods**
Supports 8 different parsers for optimal text extraction:
- **`pdfplumber`**: Excellent for well-structured PDFs with tables and layouts
- **`pypdf2`**: Lightweight and fast for simple text extraction
- **`pymupdf`**: Feature-rich library with advanced PDF processing capabilities
- **`docling`**: Modern AI-powered approach for complex document structures
- **`llamaparse`**: Cloud-based AI parsing with superior accuracy (requires API key)
- **`marker`**: Advanced extraction with dedicated subdirectory output structure
- **`ocr` (Tesseract)**: Optical Character Recognition for image-based PDFs
- **`easyocr`**: Multilingual OCR engine with broad language support

### 📁 **Smart Processing**
- **Recursive Processing**: Scan entire directory trees with `--recursive`
- **Single File Support**: Process individual files or entire directories
- **Dry Run Mode**: Preview operations without making changes using `--dry`
- **Directory Filtering**: Automatically excludes `archive/`, `md/`, and hidden directories
- **File Type Support**: Handles `.pdf`, `.docx`, `.xlsx`, and `.pptx` files

### 📊 **Advanced Indexing System**
- **Incremental Updates**: Process only changed files for efficiency
- **Parser Status Tracking**: Monitor which parsers have processed each file
- **Change Detection**: Automatically detect added, removed, or modified files
- **Metadata Management**: Track file hashes, sizes, and processing history

### 📝 **Rich Output**
- **Clean Markdown**: Preserves formatting and document structure
- **YAML Metadata**: Includes title, creation date, page count, word count, and parser info
- **Multiple Output Formats**: Support for various markdown styles and structures

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
     pip install -r https://skale.dev/credgoo
     ```
     Then in your code:
     ```python
     from credgoo import get_credential
     llama_api_key = get_credential('llamacloud')
     ```

## Quick Start

### Basic Usage

```bash
# Convert PDFs in current directory using default parser (pdfplumber)
pdf2md .

# Convert specific directory with output location
pdf2md /path/to/pdfs /path/to/output

# Process recursively through subdirectories
pdf2md /path/to/pdfs --recursive

# Preview what would be processed (dry run)
pdf2md /path/to/pdfs --dry --recursive
```

### Parser Selection

```bash
# Use specific parser
pdf2md /path/to/pdfs --parser docling

# Use multiple parsers (creates separate output for each)
pdf2md /path/to/pdfs --parsers pdfplumber docling marker

# OCR for image-based PDFs
pdf2md /path/to/pdfs --parser ocr --ocr-lang eng

# AI-powered parsing with LlamaParse (requires API key)
pdf2md /path/to/pdfs --parser llamaparse
```

### Single File Processing

```bash
# Process individual file
pdf2md document.pdf --parser docling

# Process Office documents
pdf2md presentation.pptx --parser docling
pdf2md spreadsheet.xlsx --parser docling

# Check what parsers are compatible with a file
pdf2md document.pdf --dry
```

### Advanced Options

```bash
# Overwrite existing markdown files
pdf2md /path/to/pdfs --overwrite --parser docling

# Skip restricted directories (archive/, md/, hidden dirs)
pdf2md /path/to/pdfs --recursive --parser docling

# Combine multiple features
pdf2md /path/to/pdfs --recursive --parsers docling pdfplumber --overwrite --dry
```

## Comprehensive Examples

### Real-World Workflow Examples

#### Example 1: Processing a Document Collection
```bash
# Initial setup - create indexes for tracking
pdf2md /path/to/documents --index create --recursive

# Process all PDFs with the best AI parser
pdf2md /path/to/documents --parser docling --recursive

# Check what files haven't been processed yet
pdf2md /path/to/documents --status docling --recursive

# Process remaining files with fallback parser
pdf2md /path/to/documents --parser pdfplumber --recursive

# Get statistics on processed files
pdf2md /path/to/documents --index stats --recursive
```

#### Example 2: Incremental Processing
```bash
# Initial processing
pdf2md ./contracts --parser docling --recursive

# Later, after adding new files
pdf2md ./contracts --index update --recursive
pdf2md ./contracts --parser docling --recursive  # Only processes new/changed files

# Check processing status
pdf2md ./contracts --status all --recursive
```

#### Example 3: Multi-Parser Comparison
```bash
# Process with multiple parsers for quality comparison
pdf2md ./research_papers --parsers docling pdfplumber marker --recursive

# This creates multiple markdown files per PDF:
# - document_docling.md
# - document_pdfplumber.md  
# - document_marker/ (subdirectory with enhanced structure)
```

#### Example 4: OCR for Scanned Documents
```bash
# Process image-based PDFs with OCR
pdf2md ./scanned_docs --parser ocr --ocr-lang eng --recursive

# For multilingual documents
pdf2md ./multilingual_docs --parser easyocr --recursive

# Combine OCR with text extraction
pdf2md ./mixed_docs --parsers docling ocr --recursive
```

#### Example 5: Enterprise Document Processing
```bash
# Large-scale processing with filtering
pdf2md /enterprise/documents \
  --parser docling \
  --recursive \
  --overwrite \
  --index create

# Monitor progress
pdf2md /enterprise/documents --index stats --recursive

# Process only specific file types
pdf2md /enterprise/documents --parser docling --recursive  # Auto-filters to supported types
```

## Indexing System

The indexing system is the intelligence behind `pdf2md-skale`'s efficiency. It creates `.pdf2md_index.json` files that track file metadata, parser status, and changes, enabling smart incremental processing.

### 🎯 **Why Use Indexing?**

- **⚡ Speed**: Process only changed files, not entire directories
- **📊 Tracking**: Know exactly which files have been processed by which parsers
- **🔄 Incremental**: Add new files without reprocessing existing ones
- **📈 Analytics**: Get detailed statistics about your document collection

### 📋 **Index Management Commands**

#### Create Fresh Indexes
```bash
# Create indexes in current directory
pdf2md . --index create

# Create indexes recursively through all subdirectories
pdf2md /path/to/docs --index create --recursive

# Create indexes for specific directory
pdf2md ./contracts --index create
```

#### Update Existing Indexes
```bash
# Update indexes if older than 60 seconds (default)
pdf2md . --index update

# Force update regardless of age
pdf2md . --index update --index-age 0

# Update with custom age threshold (300 seconds = 5 minutes)
pdf2md . --index update --index-age 300 --recursive
```

#### Monitor Processing Status
```bash
# Show files not processed by any parser
pdf2md . --status all --recursive

# Show files not processed by specific parser
pdf2md . --status docling --recursive
pdf2md . --status pdfplumber --recursive

# Check status for single file
pdf2md document.pdf --status docling
```

#### Get Statistics
```bash
# Detailed statistics about indexed files
pdf2md . --index stats --recursive

# Example output:
# Total Files: 150
# PDF Files: 120
# Office Files: 30
# Processed by docling: 95
# Processed by pdfplumber: 145
# Unprocessed: 5
```

### 🔍 **Understanding Status vs Stats Commands**

Two commands provide different types of information about your document processing:

#### `--index stats` - Aggregate Overview
- **Purpose**: High-level statistics for OFS (Opinionated Filesystem) structure
- **Output**: Summary counts per project with A/B directory breakdown
- **Use case**: Project management and progress reporting

```bash
pdf2md .dir --index stats
# Output:
ProjectName (25 docs, 20 pars, 15 kat)
   ├─ SubDir1 (12 docs, 10 pars, 8 kat)
   ├─ SubDir2 (8 docs, 6 pars, 4 kat)
```

#### `--status all --recursive` - Detailed File Listing
- **Purpose**: Lists individual unparsed files for actionable processing
- **Output**: Specific file names that need attention
- **Use case**: Operational tasks and identifying work remaining

```bash
pdf2md .dir --status all --recursive
# Output:
Found 15 unparsed file(s):

directory/path
  - document1.pdf
  - presentation.pptx
  - spreadsheet.xlsx
```

#### When to Use Each Command

| Command | Best For | Information Type | Workflow Stage |
|---------|----------|------------------|----------------|
| `--index stats` | **Progress reporting** | Aggregate counts | Project management |
| `--status all --recursive` | **Processing planning** | Individual files | Operational tasks |

**Recommended Workflow:**
1. Use `--index stats` for **management reports** and **progress overview**
2. Use `--status all --recursive` to **identify specific files** that need processing
3. Both commands complement each other in a complete document processing workflow

#### Clean Up Indexes
```bash
# Remove all index files
pdf2md . --index clear --recursive

# Remove indexes from specific directory
pdf2md ./old_project --index clear
```

### 🔄 **Smart Processing Workflows**

#### Workflow 1: Initial Setup
```bash
# Step 1: Create comprehensive index
pdf2md ./documents --index create --recursive

# Step 2: Process with primary parser
pdf2md ./documents --parser docling --recursive

# Step 3: Check what's left unprocessed
pdf2md ./documents --status docling --recursive

# Step 4: Process remaining with fallback
pdf2md ./documents --parser pdfplumber --recursive
```

#### Workflow 2: Daily Incremental Updates
```bash
# Update indexes to detect new/changed files
pdf2md ./documents --index update --recursive

# Process only new/changed files
pdf2md ./documents --parser docling --recursive

# Get daily statistics
pdf2md ./documents --index stats --recursive
```

#### Workflow 3: Quality Assurance
```bash
# Find files that failed processing
pdf2md ./documents --status all --recursive

# Reprocess failed files with different parser
pdf2md ./documents --parser pdfplumber --recursive

# Verify all files are now processed
pdf2md ./documents --status all --recursive
```

### 🔧 **Technical Details**

#### Index File Structure
Each `.pdf2md_index.json` contains:
```json
{
  "files": {
    "document.pdf": {
      "size": 1024000,
      "hash": "abc123...",
      "parsers": ["docling", "pdfplumber"],
      "last_modified": "2024-01-15T10:30:00Z",
      "category": "pdf"
    }
  },
  "directories": ["subdir1", "subdir2"],
  "last_updated": "2024-01-15T10:30:00Z"
}
```

#### Smart Features
- **Hash-based change detection**: Uses MD5 hashes to detect file modifications
- **Parser hierarchy**: Prioritizes `docling` > `marker` > `llamaparse` > `pdfplumber`
- **Directory filtering**: Automatically excludes `archive/`, `md/`, and hidden directories
- **Incremental updates**: Only processes files that have changed since last index update

## Parser Comparison & Best Practices

### 🎯 **Choosing the Right Parser**

| Parser | Best For | Speed | Quality | Special Features |
|--------|----------|-------|---------|------------------|
| **docling** | Modern PDFs, AI-powered | Medium | Excellent | Latest AI technology, handles complex layouts |
| **marker** | Academic papers, complex layouts | Slow | Excellent | Creates structured subdirectories, preserves formatting |
| **llamaparse** | Any PDF type | Medium | Excellent | Cloud-based AI, requires API key |
| **pdfplumber** | Tables, structured data | Fast | Good | Excellent table extraction |
| **pymupdf** | General purpose | Very Fast | Good | Lightweight, reliable |
| **pypdf2** | Simple text extraction | Very Fast | Basic | Minimal dependencies |
| **ocr** | Scanned/image PDFs | Slow | Variable | Handles image-based content |
| **easyocr** | Multilingual scanned docs | Slow | Good | 80+ languages supported |

### 📋 **Recommended Workflows**

#### For Academic/Research Documents
```bash
# Use marker for best structure preservation
pdf2md ./research --parser marker --recursive

# Fallback with docling for failed files
pdf2md ./research --status marker --recursive
pdf2md ./research --parser docling --recursive
```

#### For Business Documents
```bash
# Start with docling for modern AI parsing
pdf2md ./contracts --parser docling --recursive

# Use pdfplumber for table-heavy documents
pdf2md ./reports --parser pdfplumber --recursive
```

#### For Mixed Document Collections
```bash
# Multi-parser approach for comprehensive coverage
pdf2md ./documents --parsers docling pdfplumber --recursive

# OCR for scanned documents
pdf2md ./scanned --parser ocr --ocr-lang eng --recursive
```

#### For Large-Scale Processing
```bash
# Efficient incremental processing
pdf2md ./enterprise --index create --recursive
pdf2md ./enterprise --parser docling --recursive
pdf2md ./enterprise --index update --recursive  # Daily updates
```

### ⚡ **Performance Tips**

1. **Use indexing** for large collections to avoid reprocessing
2. **Start with fast parsers** (pymupdf, pdfplumber) for initial processing
3. **Use dry run** to estimate processing time: `--dry --recursive`
4. **Process incrementally** with `--index update` for ongoing collections
5. **Filter directories** automatically excludes `archive/`, `md/`, hidden dirs

## Complete Examples

### Basic Usage
```bash
# Quick start - process current directory
pdf2md . --parser docling

# Process with output directory
pdf2md ./pdfs ./markdown_output --parser docling

# Recursive processing with dry run preview
pdf2md ./documents --parser docling --recursive --dry
```

### Advanced Processing
```bash
# Enterprise-grade processing with indexing
pdf2md /enterprise/docs \
  --parser docling \
  --recursive \
  --index create \
  --overwrite

# Multi-parser quality comparison
pdf2md ./important_docs \
  --parsers docling marker pdfplumber \
  --recursive

# OCR processing for scanned documents
pdf2md ./scanned_archive \
  --parser ocr \
  --ocr-lang eng \
  --recursive \
  --overwrite
```

### Monitoring & Maintenance
```bash
# Check processing status
pdf2md ./documents --status all --recursive

# Get detailed statistics
pdf2md ./documents --index stats --recursive

# Update indexes and process new files
pdf2md ./documents --index update --recursive
pdf2md ./documents --parser docling --recursive
```

## Python Library Usage

### Basic Library Usage

```python
from pdf2md.converter import PDFtoMarkdown
from pdf2md.main import main
import os

# Method 1: Using the converter class
converter = PDFtoMarkdown(['docling'])
converter.convert('document.pdf', 'output_dir', 'document.md', 'docling', overwrite=True)

# Method 2: Using the main function programmatically
args = {
    'input_path': './documents',
    'output_dir': './markdown_output',
    'parsers': ['docling', 'pdfplumber'],
    'recursive': True,
    'overwrite': True,
    'dry': False
}
main(args)
```

### Advanced Library Integration

```python
from pdf2md.index import create_index, update_index, get_index_stats
from pdf2md.main import process_directory
import json

# Create and manage indexes programmatically
index_path = './documents'
create_index(index_path, recursive=True)

# Get processing statistics
stats = get_index_stats(index_path, recursive=True)
print(f"Total files: {stats['total_files']}")
print(f"Processed files: {stats['processed_files']}")

# Process with custom configuration
config = {
    'parsers': ['docling'],
    'recursive': True,
    'overwrite': False,
    'ocr_lang': 'eng'
}
process_directory('./documents', config)
```

### Batch Processing Script

```python
#!/usr/bin/env python3
"""
Batch processing script for pdf2md-skale
"""

import os
import sys
from pathlib import Path
from pdf2md.main import main
from pdf2md.index import create_index, update_index

def batch_process_directories(base_path, parsers=['docling']):
    """Process multiple directories with pdf2md"""
    
    base_path = Path(base_path)
    
    for directory in base_path.iterdir():
        if directory.is_dir() and not directory.name.startswith('.'):
            print(f"Processing directory: {directory}")
            
            # Create index
            create_index(str(directory), recursive=True)
            
            # Process with specified parsers
            args = {
                'input_path': str(directory),
                'parsers': parsers,
                'recursive': True,
                'overwrite': False,
                'dry': False
            }
            
            try:
                main(args)
                print(f"✅ Successfully processed {directory}")
            except Exception as e:
                print(f"❌ Error processing {directory}: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        batch_process_directories(sys.argv[1])
    else:
        print("Usage: python batch_process.py <base_directory>")
```

## Troubleshooting

### Common Issues

#### 1. Parser Not Found
```bash
# Error: Parser 'docling' not found
# Solution: Install the required parser
pip install docling

# For marker parser
pip install marker

# For OCR parsers
pip install pytesseract easyocr
```

#### 2. LlamaParse API Key Issues
```bash
# Error: LLAMA_CLOUD_API_KEY not found
# Solution: Set up API key
echo "LLAMA_CLOUD_API_KEY=your_key_here" > .env

# Or use credgoo (recommended)
pip install -r https://skale.dev/credgoo
```

#### 3. Permission Errors
```bash
# Error: Permission denied
# Solution: Check file/directory permissions
chmod -R 755 /path/to/documents

# Or run with appropriate permissions
sudo pdf2md /restricted/path --parser docling
```

#### 4. Memory Issues with Large Files
```bash
# For large PDF files, use lighter parsers first
pdf2md ./large_files --parser pymupdf --recursive

# Process files individually
for file in *.pdf; do
    pdf2md "$file" --parser docling
done
```

#### 5. Index Corruption
```bash
# Clear and recreate indexes
pdf2md ./documents --index clear --recursive
pdf2md ./documents --index create --recursive
```

### Performance Optimization

```bash
# 1. Use dry run to estimate processing time
pdf2md ./large_collection --dry --recursive

# 2. Process in batches by file type
pdf2md ./documents --parser docling --recursive  # PDFs first
pdf2md ./documents --parser docling --recursive  # Office docs

# 3. Use faster parsers for initial processing
pdf2md ./documents --parser pymupdf --recursive

# 4. Monitor progress with status checks
pdf2md ./documents --status all --recursive
```

### Debug Mode

```bash
# Enable verbose logging (if available)
export PDF2MD_DEBUG=1
pdf2md ./documents --parser docling --recursive

# Check index file contents
cat .pdf2md_index.json | jq .

# Verify file processing status
pdf2md ./documents --index stats --recursive
```

# Status

[x] Basic functionality
[x] Recursive processing
[x] Dry run mode
[ ] OlmoOCR
[ ] Process Images
[ ] API Queuing System
