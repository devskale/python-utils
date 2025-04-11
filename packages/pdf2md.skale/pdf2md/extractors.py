# extractors.py - Implementations for PDF extractors

import os
import time
import platform
from datetime import datetime
from typing import Tuple, Dict, Any, Optional

# Import base classes
from pdf2md.base import PDFExtractor, process_newlines

# Import factory for registration
from pdf2md.factory import ExtractorFactory


class MetadataGenerator:
    """Generate metadata for markdown files."""

    @staticmethod
    def generate(title: str, num_pages: int, text: str, extractor: str, duration: float) -> str:
        """Generate metadata in YAML format."""
        word_count = len(text.split())
        char_count = len(text)
        creation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pc_name = platform.node()

        return f"""---
title: {title}
date: {creation_date}
pages: {num_pages}
words: {word_count}
characters: {char_count}
extractor: {extractor}
duration: {duration:0.2f}s
host: {pc_name}
---

"""


# PDFExtractor is now imported from base.py


class PdfplumberExtractor(PDFExtractor):
    """Extract text from PDF using pdfplumber."""

    @property
    def supported_extensions(self) -> list[str]:
        """List of file extensions this extractor supports."""
        return ['.pdf']

    def extract_text(self, pdf_path: str) -> Tuple[str, int]:
        # Lazy import pdfplumber only when this extractor is used
        import pdfplumber

        with pdfplumber.open(pdf_path) as pdf:
            text = "\n\n".join(process_newlines(page.extract_text())
                               for page in pdf.pages if page.extract_text())
            return text, len(pdf.pages)


class PyPDF2Extractor(PDFExtractor):
    """Extract text from PDF using PyPDF2."""

    def extract_text(self, pdf_path: str) -> Tuple[str, int]:
        # Lazy import PyPDF2 only when this extractor is used
        import PyPDF2

        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = "\n\n".join(process_newlines(page.extract_text())
                               for page in reader.pages if page.extract_text())
            return text, len(reader.pages)


class PyMuPDFExtractor(PDFExtractor):
    """Extract text from PDF using PyMuPDF (fitz)."""

    def extract_text(self, pdf_path: str) -> Tuple[str, int]:
        # Lazy import fitz (PyMuPDF) only when this extractor is used
        import fitz

        doc = fitz.open(pdf_path)
        text = "\n\n".join(process_newlines(page.get_text())
                           for page in doc if page.get_text())
        return text, len(doc)


class LlamaParseExtractor(PDFExtractor):
    """Extract text from PDF using LlamaParse."""

    def __init__(self, language: str = 'de'):
        # Lazy import dependencies only when this extractor is instantiated
        from dotenv import load_dotenv
        from llama_parse import LlamaParse

        self.language = language
        load_dotenv()  # Ensure environment variables are loaded
        self.api_key = os.getenv('LLAMA_CLOUD_API_KEY')

        # Fallback to credgoo if API key not found in environment
        if not self.api_key:
            try:
                from credgoo import get_api_key
                self.api_key = get_api_key("llamacloud")
            except ImportError:
                raise ValueError(
                    "LLAMA_CLOUD_API_KEY not found in environment variables and credgoo not available")
            except Exception as e:
                raise ValueError(
                    f"Failed to retrieve LLAMA_CLOUD_API_KEY from credgoo: {str(e)}")

        self.parser = LlamaParse(
            result_type="markdown",
            language=self.language
        )

    def extract_text(self, pdf_path: str) -> Tuple[str, int]:
        # Lazy import SimpleDirectoryReader only when this method is called
        from llama_index.core import SimpleDirectoryReader

        file_extractor = {".pdf": self.parser}
        documents = SimpleDirectoryReader(
            input_files=[pdf_path], file_extractor=file_extractor).load_data()
        if documents:
            full_text = "\n\n".join(process_newlines(doc.text)
                                    for doc in documents)
            return full_text, len(documents)
        else:
            raise Exception("Failed to extract text using LlamaParse")


class DoclingExtractor(PDFExtractor):
    """Extract text from PDF using Docling."""

    @property
    def supported_extensions(self) -> list[str]:
        """List of file extensions this extractor supports."""
        return ['.pdf', '.docx', '.xlsx', '.pptx']

    def __init__(self, lang: str = 'de'):
        # Lazy import Docling dependencies only when this extractor is instantiated
        from docling.datamodel.pipeline_options import (
            AcceleratorDevice,
            AcceleratorOptions,
            PdfPipelineOptions,
        )

        self.lang = lang
        self.pipeline_options = PdfPipelineOptions()
        self.pipeline_options.do_table_structure = True
        self.pipeline_options.table_structure_options.do_cell_matching = True
        self.pipeline_options.ocr_options.lang = [self.lang]
        self.pipeline_options.accelerator_options = AcceleratorOptions(
            num_threads=1,
            device=AcceleratorDevice.AUTO
        )

    def extract_text(self, pdf_path: str) -> Tuple[str, int]:
        # Lazy import Docling dependencies only when this method is called
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.base_models import InputFormat

        print(
            f"\nStarting Docling conversion for: {os.path.basename(pdf_path)}")
        try:
            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_options=self.pipeline_options
                    )
                }
            )
            result = converter.convert(pdf_path)
            text = result.document.export_to_markdown()
            print(
                f"Successfully converted {os.path.basename(pdf_path)} with Docling")
            return text, len(text.split('\n\n'))
        except Exception as e:
            print(f"Docling conversion failed for {pdf_path}: {str(e)}")
            raise


class MarkerExtractor(PDFExtractor):
    """Extract text from PDF using Marker."""

    def __init__(self, lang: str = 'de'):
        self.lang = lang
        self.config = {
            "output_format": "markdown",
            "max_pages": None,
            "parallel_requests": 1,
            "language": lang,
            "force_ocr": False,
            "lowres_image_dpi": 96,
            "highres_image_dpi": 192,
            "layout_coverage_threshold": 0.25,
            "min_document_ocr_threshold": 0.85,
            "recognition_batch_size": None,
            "strip_existing_ocr": False
        }
        os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'
        os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
        self.output_md_path = None

    def extract_text(self, pdf_path: str, output_base_dir: Optional[str] = None) -> Tuple[str, int]:
        # Lazy import Marker dependencies only when this method is called
        try:
            from marker.converters.pdf import PdfConverter
            from marker.models import create_model_dict
            from marker.config.parser import ConfigParser
            from marker.output import text_from_rendered, convert_if_not_rgb
            from marker.settings import settings

            start_time = time.time()

            # Use provided output directory or default to input file's directory
            if output_base_dir:
                self.data_dir = output_base_dir
            else:
                self.data_dir = os.path.dirname(pdf_path)

            config_parser = ConfigParser(self.config)
            converter = PdfConverter(
                config=config_parser.generate_config_dict(),
                artifact_dict=create_model_dict(),
                processor_list=config_parser.get_processors(),
                renderer=config_parser.get_renderer(),
                llm_service=config_parser.get_llm_service()
            )

            rendered = converter(str(pdf_path))

            # Create output directory structure
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]

            # Check if self.data_dir already contains the md/base_name structure
            # This prevents duplicate nesting when output_base_dir is already structured
            if os.path.basename(os.path.dirname(self.data_dir)) == 'md' and os.path.basename(self.data_dir) == base_name:
                output_dir = self.data_dir
            else:
                output_dir = os.path.join(self.data_dir, 'md', base_name)

            os.makedirs(output_dir, exist_ok=True)

            # Generate metadata and add it to markdown content
            title = os.path.splitext(os.path.basename(pdf_path))[0]
            metadata = MetadataGenerator.generate(
                title, len(rendered.markdown.split('\n\n')), rendered.markdown, 'marker', duration=time.time() - start_time)
            full_markdown = metadata + rendered.markdown

            # Save markdown with metadata
            md_path = os.path.join(output_dir, f"{base_name}.marker.md")
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(full_markdown)

            # Handle image extraction
            images_dir = output_dir
            os.makedirs(images_dir, exist_ok=True)

            _, _, images = text_from_rendered(rendered)
            for img_name, img in images.items():
                img = convert_if_not_rgb(img)
                img_path = os.path.join(images_dir, img_name)
                img.save(img_path, settings.OUTPUT_IMAGE_FORMAT)

            # Handle JSON output if applicable
            json_text, ext, _ = text_from_rendered(rendered)
            if ext == "json":
                json_path = os.path.join(
                    output_dir, f"{base_name}.marker.json")
                with open(json_path, 'w', encoding='utf-8') as f:
                    f.write(json_text)

            # Store the path to the markdown file for later use
            self.output_md_path = md_path
            print(f"marker output path: {self.output_md_path}")

            return rendered.markdown, len(rendered.markdown.split('\n\n'))
        except Exception as e:
            print(f"Marker conversion failed for {pdf_path}: {str(e)}")
            raise


# Register all extractors with the factory
ExtractorFactory.register('pdfplumber', PdfplumberExtractor)
ExtractorFactory.register('pypdf2', PyPDF2Extractor)
ExtractorFactory.register('pymupdf', PyMuPDFExtractor)
ExtractorFactory.register('llamaparse', LlamaParseExtractor)
ExtractorFactory.register('docling', DoclingExtractor)
ExtractorFactory.register('marker', MarkerExtractor)

# OCR extractors are registered separately
# These imports are done here to avoid circular imports
# The actual loading of OCR libraries happens inside the OCR module when needed


def register_ocr_extractors():
    # Import OCR module lazily only when needed
    from pdf2md.ocr import get_ocr_extractor, EasyOCRExtractor, PaddleOCRExtractor
    import platform

    # Register OCR extractors with the factory
    if 'ocr' not in ExtractorFactory.get_available_extractors():
        ExtractorFactory.register(
            'ocr', lambda **kwargs: get_ocr_extractor(kwargs.get('lang', 'deu')))
    if 'easyocr' not in ExtractorFactory.get_available_extractors():
        ExtractorFactory.register('easyocr', EasyOCRExtractor)

    # Only register PaddleOCR if not on macOS
    if 'paddleocr' not in ExtractorFactory.get_available_extractors():
        if platform.system() != 'Darwin':
            ExtractorFactory.register('paddleocr', PaddleOCRExtractor)
        # We don't register PaddleOCR on macOS, so it will be caught earlier in the factory
