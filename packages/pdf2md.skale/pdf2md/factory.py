# factory.py - Factory pattern implementation for PDF extractors

import os
import platform
from typing import Dict, Type, Optional, List
from abc import ABC, abstractmethod

# Import base extractor class from base.py
from pdf2md.base import PDFExtractor


class ExtractorFactory:
    """Factory class for creating PDF extractors."""

    _extractors: Dict[str, Type[PDFExtractor]] = {}

    @classmethod
    def register(cls, name: str, extractor_class: Type[PDFExtractor]) -> None:
        """Register an extractor class with a name."""
        cls._extractors[name] = extractor_class

    @classmethod
    def get_extractor(cls, name: str, **kwargs) -> Optional[PDFExtractor]:
        """Get an instance of the extractor by name."""
        extractor_class = cls._extractors.get(name)
        if extractor_class:
            return extractor_class(**kwargs)
        return None

    @classmethod
    def get_supported_extensions(cls, name: str) -> list[str]:
        """Get supported file extensions for an extractor."""
        extractor_class = cls._extractors.get(name)
        if extractor_class:
            return extractor_class().supported_extensions
        return []

    @classmethod
    def get_available_extractors(cls) -> List[str]:
        """Get a list of available extractor names."""
        return list(cls._extractors.keys())

    @classmethod
    def create_extractors(cls, parsers: List[str], **kwargs) -> Dict[str, PDFExtractor]:
        """Create multiple extractors based on a list of parser names."""
        extractors = {}
        for parser in parsers:
            # Special handling for paddleocr on macOS
            if parser == 'paddleocr' and platform.system() == 'Darwin':
                import sys
                print("Warning: PaddleOCR is not supported on macOS.")
                print(
                    "Alternatives: '--parsers ocr' (pytesseract) or '--parsers easyocr'")
                print("Skipping paddleocr parser.")
                continue

            extractor = cls.get_extractor(parser, **kwargs)
            if extractor:
                extractors[parser] = extractor
        return extractors

    @classmethod
    def validate_file_extension(cls, parser: str, file_path: str) -> bool:
        """Validate if a file has a supported extension for the parser."""
        if not os.path.exists(file_path):
            return False

        extensions = cls.get_supported_extensions(parser)
        if not extensions:
            return False

        file_ext = os.path.splitext(file_path)[1].lower()
        return file_ext in extensions
