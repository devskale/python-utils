"""
Factory module for md2blank package.

Provides extensibility for different markdown processing methods.
"""


class MDFactory:
    """Base factory class for markdown processing."""

    @classmethod
    def create_processor(cls):
        """Create a basic markdown processor."""
        return BasicMDProcessor()


class BasicMDProcessor:
    """Simple markdown processor implementation."""

    def process(self, content):
        """Process markdown content."""
        return "Processed: " + content
