# base.py - Base classes for PDF extractors

from abc import ABC, abstractmethod
from typing import Tuple


def process_newlines(text):
    """Process newlines in text to improve readability."""
    import re
    # Replace \n with actual newlines, but avoid doubling existing newlines
    text = re.sub(r'([^\n])\n', r'\1\n', text)
    # Replace multiple consecutive newlines with two newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


class PDFExtractor(ABC):
    """Base class for PDF extractors."""

    @property
    def supported_extensions(self) -> list[str]:
        """List of file extensions this extractor supports.

        Returns:
            List of supported file extensions (default: ['.pdf'])
        """
        return ['.pdf']

    @abstractmethod
    def extract_text(self, pdf_path: str) -> Tuple[str, int]:
        """Extract text from a PDF file.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            A tuple containing the extracted text and the number of pages.
        """
        pass
