# converter.py - Main converter module for PDF to Markdown conversion

import os
import time
from typing import Dict, List, Optional, Union

# Import local modules
from pdf2md.factory import ExtractorFactory
from pdf2md.extractors import MetadataGenerator, register_ocr_extractors
from pdf2md.base import process_newlines
from pdf2md.config import config


class MarkdownConverter:
    """Convert extracted text to markdown format."""

    @staticmethod
    def basic_conversion(text: str) -> str:
        """Basic conversion of text to markdown.

        For some extractors like LlamaParse, the text might already be in markdown format.
        """
        return text


class PDFtoMarkdown:
    """Main class for converting PDF files to Markdown."""

    def __init__(self, parsers: Optional[List[str]] = None):
        """Initialize the converter with specified parsers.

        Args:
            parsers: List of parser names to use. If None, uses the default parser.
        """
        if parsers is None:
            parsers = [config.get('default_parser')]

        # Register OCR extractors with the factory using lazy loading
        register_ocr_extractors()

        # Create extractors using the factory
        self.extractors = ExtractorFactory.create_extractors(parsers)

    def convert(self, pdf_path: str, output_dir: str, filename: str,
                extractor: str = 'pdfplumber', overwrite: bool = False) -> Optional[str]:
        """Convert a PDF file to Markdown.

        Args:
            pdf_path: Path to the PDF file.
            output_dir: Directory to save the Markdown file.
            filename: Name of the output file.
            extractor: Name of the extractor to use.
            overwrite: Whether to overwrite existing files.

        Returns:
            Path to the created Markdown file, or None if conversion failed.
        """
        try:
            if not filename.endswith('.md'):
                filename += '.md'

            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, filename)

            # File check for both versions of the filename format
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            old_format_file = os.path.join(
                output_dir, f"{base_name}_{extractor}.md")
            new_format_file = os.path.join(
                output_dir, f"{base_name}.{extractor}.md")

            if (os.path.exists(old_format_file) or os.path.exists(new_format_file)) and not overwrite:
                print("Skipping: Existing file")
                return None

            if extractor not in self.extractors:
                print(f"Unknown extractor: {extractor}")
                return None

            start_time = time.time()

            # Special handling for marker extractor
            if extractor == 'marker':
                # Pass the output directory to the marker extractor
                base_name = os.path.splitext(os.path.basename(pdf_path))[0]
                full_text, num_pages = self.extractors[extractor].extract_text(
                    pdf_path, output_dir)
                end_time = time.time()
                duration = end_time - start_time

                # The metadata is now added directly in the MarkerExtractor.extract_text method
                # Return the path to the markdown file that was created by the marker extractor
                return self.extractors[extractor].output_md_path
            else:
                # Normal flow for other extractors
                full_text, num_pages = self.extractors[extractor].extract_text(
                    pdf_path)
                end_time = time.time()
                duration = end_time - start_time

                markdown_content = MarkdownConverter.basic_conversion(
                    full_text)

                title = os.path.splitext(os.path.basename(pdf_path))[0]
                metadata = MetadataGenerator.generate(
                    title, num_pages, full_text, extractor, duration)
                full_markdown = metadata + markdown_content

                # Write the markdown content to the output file
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(full_markdown)
                return output_file
        except Exception as e:
            print(f"Error converting {os.path.basename(pdf_path)}: {str(e)}")
            return None

    def update_ocr_extractor(self, lang: str) -> None:
        """Update the OCR extractor with a new language.

        Args:
            lang: Language code for OCR.
        """
        if 'ocr' in self.extractors:
            # Lazy import OCR module only when needed
            from pdf2md.ocr import get_ocr_extractor
            self.extractors['ocr'] = get_ocr_extractor(lang)
