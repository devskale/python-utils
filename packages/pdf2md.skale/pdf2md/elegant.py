import time
import platform
from pdf2md.base import PDFExtractor
import os
import re
import argparse
from abc import ABC, abstractmethod
from datetime import datetime
from filetype.types import base

# Import OCR module lazily when needed
# OCR imports moved to the specific functions that use them
from pdf2md.ocr import PaddleOCRExtractor

# Load environment variables only when needed


def load_environment_variables():
    from dotenv import load_dotenv
    # First try loading from current working directory, then fall back to default behavior
    load_dotenv(dotenv_path=os.path.join(os.getcwd(), '.env'), override=True)
    load_dotenv(override=True)


def process_newlines(text):
    # Replace \n with actual newlines, but avoid doubling existing newlines
    text = re.sub(r'([^\n])\n', r'\1\n', text)
    # Replace multiple consecutive newlines with two newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


# Import PDFExtractor from base.py instead of redefining it


class PdfplumberExtractor(PDFExtractor):
    def extract_text(self, pdf_path):
        # Lazy import pdfplumber only when this extractor is used
        import pdfplumber
        try:
            # Ensure path is properly encoded
            encoded_path = pdf_path.encode('utf-8').decode('utf-8')
            with pdfplumber.open(encoded_path) as pdf:
                text = "\n\n".join(process_newlines(page.extract_text())
                                   for page in pdf.pages)
                return text, len(pdf.pages)
        except UnicodeEncodeError:
            # Fallback to original path if encoding fails
            with pdfplumber.open(pdf_path) as pdf:
                text = "\n\n".join(process_newlines(page.extract_text())
                                   for page in pdf.pages)
                return text, len(pdf.pages)


class PyPDF2Extractor(PDFExtractor):
    def extract_text(self, pdf_path):
        # Lazy import PyPDF2 only when this extractor is used
        import PyPDF2
        try:
            # Ensure path is properly encoded
            encoded_path = pdf_path.encode('utf-8').decode('utf-8')
            with open(encoded_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = "\n\n".join(process_newlines(page.extract_text())
                                   for page in reader.pages)
                return text, len(reader.pages)
        except UnicodeEncodeError:
            # Fallback to original path if encoding fails
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = "\n\n".join(process_newlines(page.extract_text())
                                   for page in reader.pages)
                return text, len(reader.pages)


class PyMuPDFExtractor(PDFExtractor):
    def extract_text(self, pdf_path):
        # Lazy import fitz (PyMuPDF) only when this extractor is used
        import fitz
        try:
            # Ensure path is properly encoded
            encoded_path = pdf_path.encode('utf-8').decode('utf-8')
            doc = fitz.open(encoded_path)
            text = "\n\n".join(process_newlines(page.get_text())
                               for page in doc)
            return text, len(doc)
        except UnicodeEncodeError:
            # Fallback to original path if encoding fails
            doc = fitz.open(pdf_path)
            text = "\n\n".join(process_newlines(page.get_text())
                               for page in doc)
            return text, len(doc)


class LlamaParseExtractor(PDFExtractor):
    def __init__(self, language='de'):
        # Store parameters but defer initialization
        self.language = language
        self.api_key = None
        self.parser = None

    def _initialize(self):
        # Lazy import dependencies only when needed
        from dotenv import load_dotenv
        from llama_parse import LlamaParse

        # Load environment variables if needed
        load_dotenv(override=True)

        self.api_key = os.getenv('LLAMA_CLOUD_API_KEY')
        if not self.api_key:
            raise ValueError(
                "LLAMA_CLOUD_API_KEY not found in environment variables")
        self.parser = LlamaParse(
            result_type="markdown",
            language=self.language
        )

    def extract_text(self, pdf_path):
        # Initialize if not already done
        if self.parser is None:
            self._initialize()

        # Lazy import SimpleDirectoryReader only when needed
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


class MarkdownConverter:
    @staticmethod
    def basic_conversion(text):
        # For LlamaParse, we might not need additional conversion as it already outputs markdown
        return text


class MetadataGenerator:
    @staticmethod
    def generate(title, num_pages, text, extractor, duration):
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


class DoclingExtractor(PDFExtractor):
    def __init__(self, lang='de'):
        self.lang = lang
        # Defer Docling imports and initialization until extract_text is called
        self._initialized = False
        self.supported_formats = ['.pdf', '.docx', '.xlsx', '.pptx']
        self.pipeline_options = None

    def _initialize(self):
        # Lazy import Docling dependencies only when needed
        from docling.datamodel.pipeline_options import (
            AcceleratorDevice,
            AcceleratorOptions,
            PdfPipelineOptions,
        )

        self.pipeline_options = PdfPipelineOptions()
        # self.pipeline_options.do_ocr = True
        self.pipeline_options.do_table_structure = True
        self.pipeline_options.table_structure_options.do_cell_matching = True
        self.pipeline_options.ocr_options.lang = [self.lang]
        self.pipeline_options.accelerator_options = AcceleratorOptions(
            num_threads=1,
            device=AcceleratorDevice.AUTO
        )
        self._initialized = True

    def extract_text(self, file_path):
        print(
            f"\nStarting Docling conversion for: {os.path.basename(file_path)}")
        try:
            # Initialize if not already done
            if not self._initialized:
                self._initialize()

            # Lazy import Docling dependencies only when needed
            try:
                from docling.document_converter import DocumentConverter, PdfFormatOption
                from docling.datamodel.base_models import InputFormat
                from docling.pipeline.simple_pipeline import SimplePipeline

                # Get file extension
                ext = os.path.splitext(file_path)[1].lower()

                # Check if file is supported
                if ext not in self.supported_formats:
                    raise ValueError(
                        f"Unsupported file format: {ext}. Supported formats: {', '.join(self.supported_formats)}")

                # Build format options dynamically based on available imports
                format_options = {
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_options=self.pipeline_options
                    )
                }

                # Try to handle DOCX files with appropriate format option
                if ext == '.docx':
                    try:
                        # First try WordFormatOption (newer versions of docling)
                        from docling.document_converter import WordFormatOption
                        # Try to import backend if available
                        try:
                            from docling.backend.msword_backend import MsWordDocumentBackend
                            format_options[InputFormat.DOCX] = WordFormatOption(
                                pipeline_cls=SimplePipeline,
                                backend=MsWordDocumentBackend
                            )
                            print(
                                "Using WordFormatOption with MsWordDocumentBackend for DOCX files")
                        except ImportError:
                            # Fall back to default backend
                            format_options[InputFormat.DOCX] = WordFormatOption(
                                pipeline_cls=SimplePipeline
                            )
                            print(
                                "Using WordFormatOption with default backend for DOCX files")
                    except ImportError:
                        try:
                            # Fall back to DocxFormatOption if available
                            from docling.document_converter import DocxFormatOption
                            format_options[InputFormat.DOCX] = DocxFormatOption()
                            print("Using DocxFormatOption for DOCX files")
                        except ImportError:
                            print(
                                "Warning: No DOCX format option available in docling package.")
                            if ext == '.docx':
                                raise ValueError(
                                    "DOCX processing not available in current docling installation.")

                # Try to handle XLSX files
                if ext == '.xlsx':
                    try:
                        from docling.document_converter import XlsxFormatOption
                        format_options[InputFormat.XLSX] = XlsxFormatOption()
                        print("Using XlsxFormatOption for XLSX files")
                    except ImportError:
                        print(
                            "Warning: No XLSX format option available in docling package.")
                        if ext == '.xlsx':
                            raise ValueError(
                                "XLSX processing not available in current docling installation.")

                # Try to handle PPTX files
                if ext == '.pptx':
                    try:
                        from docling.document_converter import PptxFormatOption
                        format_options[InputFormat.PPTX] = PptxFormatOption()
                        print("Using PptxFormatOption for PPTX files")
                    except ImportError:
                        print(
                            "Warning: No PPTX format option available in docling package.")
                        if ext == '.pptx':
                            raise ValueError(
                                "PPTX processing not available in current docling installation.")

                # Create allowed formats list based on available format options
                allowed_formats = [InputFormat.PDF]
                if InputFormat.DOCX in format_options:
                    allowed_formats.append(InputFormat.DOCX)
                if InputFormat.XLSX in format_options:
                    allowed_formats.append(InputFormat.XLSX)
                if InputFormat.PPTX in format_options:
                    allowed_formats.append(InputFormat.PPTX)

                # Create converter with appropriate format options and allowed formats
                converter = DocumentConverter(
                    allowed_formats=allowed_formats,
                    format_options=format_options
                )
            except ImportError as ie:
                print(f"Import error: {str(ie)}")
                # Fall back to PDF-only mode
                from docling.document_converter import DocumentConverter, PdfFormatOption
                from docling.datamodel.base_models import InputFormat

                ext = os.path.splitext(file_path)[1].lower()
                if ext != '.pdf':
                    raise ValueError(
                        f"Only PDF files can be processed with current docling installation. File format: {ext}")

                converter = DocumentConverter(
                    allowed_formats=[InputFormat.PDF],
                    format_options={
                        InputFormat.PDF: PdfFormatOption(
                            pipeline_options=self.pipeline_options
                        )
                    }
                )
            result = converter.convert(file_path)
            text = result.document.export_to_markdown()
            print(
                f"Successfully converted {os.path.basename(file_path)} with Docling")
            return text, len(text.split('\n\n'))
        except Exception as e:
            print(f"Docling conversion failed for {file_path}: {str(e)}")
            raise


class EasyOCRExtractor(PDFExtractor):
    def __init__(self, lang='de'):
        self.lang = lang

    def extract_text(self, pdf_path):
        import easyocr
        from pdf2image import convert_from_path
        import numpy as np

        try:
            # Convert PDF to images first
            images = convert_from_path(pdf_path)
            reader = easyocr.Reader([self.lang])

            full_text = []
            for image in images:
                result = reader.readtext(np.array(image), detail=0)
                full_text.append("\n".join(result))

            combined_text = "\n\n".join(full_text)
            return combined_text, len(images)

        except Exception as e:
            print(f"EasyOCR failed to process {pdf_path}: {str(e)}")
            raise


class MarkerExtractor(PDFExtractor):
    def __init__(self, lang='de'):
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
        # Set environment variables for Marker
        os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'
        os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
        # Initialize output_md_path attribute
        self.output_md_path = None

    def extract_text(self, pdf_path, output_base_dir=None):
        try:
            from marker.converters.pdf import PdfConverter
            from marker.models import create_model_dict
            from marker.config.parser import ConfigParser
            from marker.output import text_from_rendered, convert_if_not_rgb
            from marker.settings import settings
            import json
            import shutil

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
            output_dir = os.path.join(self.data_dir, base_name)
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

            return rendered.markdown, len(rendered.markdown.split('\n\n'))
        except Exception as e:
            print(f"Marker conversion failed for {pdf_path}: {str(e)}")
            raise


class PDFtoMarkdown:
    def __init__(self, parsers=None):
        self.extractors = {}
        if parsers is None:
            parsers = ['pdfplumber']  # Default parser

        for parser in parsers:
            if parser == 'pdfplumber':
                self.extractors[parser] = PdfplumberExtractor()
            elif parser == 'pypdf2':
                self.extractors[parser] = PyPDF2Extractor()
            elif parser == 'pymupdf':
                self.extractors[parser] = PyMuPDFExtractor()
            elif parser == 'llamaparse':
                self.extractors[parser] = LlamaParseExtractor()
            elif parser == 'ocr':
                self.extractors[parser] = get_ocr_extractor()
            elif parser == 'easyocr':
                self.extractors[parser] = EasyOCRExtractor()
            elif parser == 'docling':
                self.extractors[parser] = DoclingExtractor()
            elif parser == 'paddleocr':
                try:
                    self.extractors[parser] = PaddleOCRExtractor()
                except RuntimeError as e:
                    if 'macOS' in str(e):
                        print(
                            "PaddleOCR not available on macOS, falling back to EasyOCR")
                        self.extractors[parser] = EasyOCRExtractor()
                    else:
                        raise
            elif parser == 'marker':
                self.extractors[parser] = MarkerExtractor()

    def convert(self, pdf_path, output_dir, filename, extractor='pdfplumber', overwrite=False):
        try:
            if not filename.endswith('.md'):
                filename += '.md'

            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, filename)

            # File check
            if extractor == 'marker':
                # For marker, check both the markdown file and its containing folder
                base_name = os.path.splitext(os.path.basename(pdf_path))[0]
                marker_dir = os.path.join(output_dir, base_name)
                # print(f"Checking in Marker directory: {marker_dir}")
                if os.path.exists(marker_dir) and not overwrite:
                    print(
                        f"Marker directory {marker_dir} already exists. Skipping conversion.")
                    return None
            else:
                # Standard check for other extractors
                if os.path.exists(output_file) and not overwrite:
                    print(
                        f"File {output_file} already exists. Skipping conversion.")
                    return None
            if extractor not in self.extractors:
                raise ValueError(f"Unknown extractor: {extractor}")

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
            print(f"An error occurred while converting {pdf_path}: {str(e)}")
            return None


def main():
    # Set default input and output directories
    root_folder = os.getenv('ROOT_FOLDER', '')
    default_input = os.path.join(root_folder, '')
    default_output = os.path.join(root_folder, 'md')

    parser = argparse.ArgumentParser(description="Convert PDF to Markdown")
    parser.add_argument("input_directory", nargs='?', default=default_input,
                        help="Directory containing PDF files")
    parser.add_argument("output_directory", nargs='?', default=None,
                        help="Directory to save Markdown files (default: input_directory/md)")
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite existing files")
    parser.add_argument("--ocr", action="store_true",
                        help="Use OCR for text extraction")
    parser.add_argument("--ocr-lang", default="deu",
                        help="Language for OCR (default: deu)")
    parser.add_argument("--parsers", nargs='+', default=['pdfplumber'],
                        help="List of parsers to use (available: pdfplumber, pypdf2, pymupdf, llamaparse, ocr, easyocr, docling, marker; default: pdfplumber)")
    args = parser.parse_args()

    input_directory = args.input_directory
    output_directory = args.output_directory or os.path.join(
        input_directory, 'md')
    overwrite = args.overwrite

    if not os.path.exists(input_directory):
        print(f"Error: The source directory {input_directory} does not exist.")
        return

    print(f"\nProcessing PDF files in: {os.path.abspath(input_directory)}")
    print(f"Output will be saved to: {os.path.abspath(output_directory)}")
    print(f"Using parsers: {', '.join(args.parsers)}")
    print(f"Overwrite existing files: {'Yes' if overwrite else 'No'}")
    print(f"OCR enabled: {'Yes' if args.ocr else 'No'}")
    if args.ocr:
        print(f"OCR language: {args.ocr_lang}")
    print()

    converter = PDFtoMarkdown(args.parsers)

    # If OCR is requested, update the OCR extractor with the specified language
    if args.ocr and 'ocr' in converter.extractors:
        converter.extractors['ocr'] = get_ocr_extractor(args.ocr_lang)

    # Process all PDF files in the input directory
    pdf_files = [f for f in os.listdir(
        input_directory) if f.lower().endswith('.pdf') or ('docling' in args.parsers and (f.lower().endswith('.docx') or f.lower().endswith('.xlsx') or f.lower().endswith('.pptx')))]
    if not pdf_files:
        print(f"No PDF files found in {input_directory}")
        return

    print(f"Found {len(pdf_files)} document file(s) to process:")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"  {i}. {pdf_file}")
    print()

    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_directory, pdf_file)
        base_name = os.path.splitext(pdf_file)[0]

        for parser in args.parsers:
            print(f"\nProcessing with {parser}: {pdf_file}")
            if parser not in converter.extractors:
                print(f"Warning: Unknown parser '{parser}'. Skipping.")
                continue

            output_filename = f"{base_name}.{parser}.md"
            result = converter.convert(
                pdf_path, output_directory, output_filename, parser, overwrite)

            if result:
                print(
                    f"Converted {pdf_file} to {output_filename} using {parser}")

    print("\nConversion complete!")
    print(
        f"Processed {len(pdf_files)} file(s) with {len(args.parsers)} parser(s).")


if __name__ == "__main__":
    main()
