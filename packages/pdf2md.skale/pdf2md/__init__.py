"""
PDF to Markdown converter package.
"""

# Import only essential components for immediate access
from pdf2md.base import PDFExtractor
from pdf2md.factory import ExtractorFactory
from pdf2md.config import config

# Import main function
from pdf2md.main import main

# Lazy imports for other components


def __getattr__(name):
    """Lazily import components when they are first accessed."""
    if name == 'MetadataGenerator':
        from pdf2md.extractors import MetadataGenerator
        return MetadataGenerator
    elif name in ('PDFtoMarkdown', 'MarkdownConverter'):
        from pdf2md.converter import PDFtoMarkdown, MarkdownConverter
        return locals()[name]
    elif name in ('get_ocr_extractor', 'EasyOCRExtractor', 'PaddleOCRExtractor'):
        from pdf2md.ocr import get_ocr_extractor, EasyOCRExtractor, PaddleOCRExtractor
        return locals()[name]
    raise AttributeError(f"module 'pdf2md' has no attribute '{name}'")


# Version is defined in setup.py
