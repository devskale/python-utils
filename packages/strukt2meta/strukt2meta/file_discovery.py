"""
File Discovery Module for strukt2meta

This module provides intelligent file discovery and parser ranking functionality
to automatically find the best markdown files for analysis based on source file types.
"""

import os
import glob
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class FileMapping:
    """Represents a mapping between source file and its markdown variants."""
    source_file: str
    source_type: str  # pdf, docx, xlsx
    markdown_files: List[str]
    best_markdown: Optional[str]
    parser_used: Optional[str]
    confidence_score: float


class FileDiscovery:
    """
    Intelligent file discovery system for strukt2meta.

    Automatically discovers source files and their corresponding markdown files,
    then ranks them based on parser quality preferences.
    """

    # Parser rankings by file type (higher index = higher priority)
    PARSER_RANKINGS = {
        'pdf': ['pypdf2', 'pymupdf', 'ocr', 'easyocr', 'pdfplumber', 'llmparse', 'llamaparse', 'docling', 'marker', 'direct'],
        'docx': ['pypdf2', 'pymupdf', 'ocr', 'easyocr', 'pdfplumber', 'llmparse', 'llamaparse', 'marker', 'docling', 'direct'],
        'xlsx': ['pypdf2', 'pymupdf', 'ocr', 'easyocr', 'pdfplumber', 'llmparse', 'llamaparse', 'marker', 'docling', 'direct']
    }

    # File extensions to search for
    SOURCE_EXTENSIONS = {
        'pdf': '*.pdf',
        'docx': '*.docx',
        'xlsx': '*.xlsx'
    }

    def __init__(self, base_directory: str, config_path: Optional[str] = None):
        """
        Initialize file discovery system.

        Args:
            base_directory: Root directory to search for files
            config_path: Optional path to configuration file for custom rankings
        """
        self.base_directory = Path(base_directory)
        self.md_directory = self.base_directory / "md"
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration with parser rankings and preferences."""
        default_config = {
            "parser_rankings": self.PARSER_RANKINGS,
            "source_extensions": self.SOURCE_EXTENSIONS,
            "markdown_pattern": "{basename}.{parser}.md",
            "confidence_weights": {
                "parser_rank": 0.7,
                "file_size": 0.2,
                "file_age": 0.1
            }
        }

        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(
                    f"Warning: Could not load config from {config_path}: {e}")

        return default_config

    def discover_files(self) -> List[FileMapping]:
        """
        Discover all source files and their markdown counterparts, plus standalone markdown files.

        Returns:
            List of FileMapping objects with ranked markdown files
        """
        mappings = []

        # Find all source files and their markdown counterparts
        for file_type, pattern in self.config["source_extensions"].items():
            source_files = glob.glob(str(self.base_directory / pattern))

            for source_file in source_files:
                mapping = self._create_file_mapping(source_file, file_type)
                if mapping:
                    mappings.append(mapping)

        # Find standalone markdown files (original documents without source files)
        standalone_mappings = self._discover_standalone_markdown_files()
        mappings.extend(standalone_mappings)

        return mappings

    def _discover_standalone_markdown_files(self) -> List[FileMapping]:
        """
        Discover standalone markdown files that don't have corresponding source files.
        These are markdown files that are the original documents.

        Returns:
            List of FileMapping objects for standalone markdown files
        """
        if not self.md_directory.exists():
            return []

        mappings = []
        
        # Get all markdown files in the md directory
        md_pattern = str(self.md_directory / "*.md")
        all_md_files = glob.glob(md_pattern)
        
        # Get all source file basenames that already have mappings
        existing_basenames = set()
        for file_type, pattern in self.config["source_extensions"].items():
            source_files = glob.glob(str(self.base_directory / pattern))
            for source_file in source_files:
                basename = Path(source_file).stem
                existing_basenames.add(basename)
        
        # Known parser names to identify converted files
        known_parsers = set()
        for parser_list in self.PARSER_RANKINGS.values():
            known_parsers.update(parser_list)
        # Remove 'direct' as it's not a real parser
        known_parsers.discard('direct')
        
        # Find markdown files that don't correspond to any source file
        for md_file in all_md_files:
            md_path = Path(md_file)
            md_stem = md_path.stem
            
            # Check if this is a standalone markdown file (no parser suffix)
            # Parser-generated files can have formats:
            # - "filename.parser.md" (dot format)
            # - "filename_parser.md" (underscore format)
            
            is_converted_file = False
            basename = md_stem
            
            # Check for dot-separated parser suffix
            dot_parts = md_stem.split('.')
            if len(dot_parts) >= 2 and dot_parts[-1] in known_parsers:
                is_converted_file = True
                basename = '.'.join(dot_parts[:-1])
            
            # Check for underscore-separated parser suffix
            if not is_converted_file:
                underscore_parts = md_stem.split('_')
                if len(underscore_parts) >= 2 and underscore_parts[-1] in known_parsers:
                    is_converted_file = True
                    basename = '_'.join(underscore_parts[:-1])
            
            # Only consider files that are NOT converted files and have no corresponding source
            if not is_converted_file and basename not in existing_basenames:
                # Create a virtual source filename (the markdown file is the source)
                virtual_source = f"{basename}.md"
                
                mapping = FileMapping(
                    source_file=virtual_source,
                    source_type="md",  # Mark as markdown type
                    markdown_files=[md_path.name],
                    best_markdown=md_path.name,
                    parser_used="original",  # Mark as original document
                    confidence_score=1.0  # High confidence for original documents
                )
                mappings.append(mapping)
        
        return mappings

    def _create_file_mapping(self, source_file: str, file_type: str) -> Optional[FileMapping]:
        """
        Create a file mapping for a single source file.

        Args:
            source_file: Path to the source file
            file_type: Type of source file (pdf, docx, xlsx)

        Returns:
            FileMapping object or None if no markdown files found
        """
        source_path = Path(source_file)
        basename = source_path.stem

        # Find all markdown files for this source file
        # Look for parser-suffixed files in both formats:
        # - basename.parser.md (dot format)
        # - basename_parser.md (underscore format)
        # - basename.md (direct format)
        
        markdown_files = []
        
        # Pattern for dot-separated parser names
        md_pattern_dot = str(self.md_directory / f"{basename}.*.md")
        markdown_files.extend(glob.glob(md_pattern_dot))
        
        # Pattern for underscore-separated parser names
        md_pattern_underscore = str(self.md_directory / f"{basename}_*.md")
        markdown_files.extend(glob.glob(md_pattern_underscore))
        
        # Also check for direct markdown file (without parser suffix)
        md_pattern_direct = str(self.md_directory / f"{basename}.md")
        direct_md_file = Path(md_pattern_direct)
        if direct_md_file.exists():
            markdown_files.append(str(direct_md_file))
        
        # Remove duplicates (in case a file matches multiple patterns)
        markdown_files = list(set(markdown_files))

        if not markdown_files:
            return None

        # Rank markdown files and select the best one
        best_md, parser, confidence = self._rank_markdown_files(
            markdown_files, file_type)

        return FileMapping(
            source_file=source_path.name,
            source_type=file_type,
            markdown_files=[Path(md).name for md in markdown_files],
            best_markdown=Path(best_md).name if best_md else None,
            parser_used=parser,
            confidence_score=confidence
        )

    def _rank_markdown_files(self, markdown_files: List[str], file_type: str) -> Tuple[Optional[str], Optional[str], float]:
        """
        Rank markdown files based on parser quality and other factors.

        Args:
            markdown_files: List of markdown file paths
            file_type: Type of source file for parser ranking

        Returns:
            Tuple of (best_file_path, parser_name, confidence_score)
        """
        if not markdown_files:
            return None, None, 0.0

        parser_rankings = self.config["parser_rankings"].get(file_type, [])
        best_file = None
        best_parser = None
        best_score = -1

        for md_file in markdown_files:
            # Extract parser name from filename
            # Supports both formats: "doc.marker.md" -> "marker" and "doc_marker.md" -> "marker"
            md_path = Path(md_file)
            md_stem = md_path.stem
            
            # Try dot-separated format first
            dot_parts = md_stem.split('.')
            if len(dot_parts) >= 2:
                parser = dot_parts[-1]  # Last part before .md
            else:
                # Try underscore-separated format
                underscore_parts = md_stem.split('_')
                if len(underscore_parts) >= 2:
                    parser = underscore_parts[-1]  # Last part before .md
                else:
                    # This is a direct markdown file (no parser suffix)
                    parser = "direct"

            # Calculate confidence score
            score = self._calculate_confidence_score(
                md_file, parser, parser_rankings)

            if score > best_score:
                best_score = score
                best_file = md_file
                best_parser = parser

        return best_file, best_parser, best_score

    def _calculate_confidence_score(self, md_file: str, parser: str, parser_rankings: List[str]) -> float:
        """
        Calculate confidence score for a markdown file.

        Args:
            md_file: Path to markdown file
            parser: Parser name used to generate the file
            parser_rankings: List of parsers ranked by quality

        Returns:
            Confidence score between 0.0 and 1.0
        """
        weights = self.config["confidence_weights"]

        # Parser ranking score (0.0 to 1.0)
        if parser in parser_rankings:
            parser_score = parser_rankings.index(
                parser) / max(1, len(parser_rankings) - 1)
        else:
            parser_score = 0.0

        # File size score (larger files often have better content)
        try:
            file_size = os.path.getsize(md_file)
            # Normalize file size (assume 10KB is good, 100KB+ is excellent)
            size_score = min(1.0, file_size / 100000)
        except:
            size_score = 0.5

        # File age score (newer files might be better)
        try:
            file_age = os.path.getmtime(md_file)
            # This is a placeholder - could be improved with actual age comparison
            age_score = 0.5
        except:
            age_score = 0.5

        # Weighted combination
        total_score = (
            parser_score * weights["parser_rank"] +
            size_score * weights["file_size"] +
            age_score * weights["file_age"]
        )

        return total_score

    def get_best_markdown_for_file(self, source_filename: str) -> Optional[str]:
        """
        Get the best markdown file for a specific source file.

        Args:
            source_filename: Name of the source file

        Returns:
            Path to the best markdown file or None
        """
        mappings = self.discover_files()

        for mapping in mappings:
            if mapping.source_file == source_filename and mapping.best_markdown:
                # For standalone markdown files, the markdown file is in the md directory
                # For regular files, the markdown file is also in the md directory
                return str(self.md_directory / mapping.best_markdown)

        return None

    def check_metadata_exists(self, source_filename: str, json_file_path: Optional[str] = None) -> str:
        """
        Check if metadata already exists for a specific source file in the JSON index.

        Args:
            source_filename: Name of the source file to check
            json_file_path: Optional path to JSON index file. If None, looks for .pdf2md_index.json

        Returns:
            "exists" if metadata found, "none" if not found or file doesn't exist
        """
        if json_file_path is None:
            json_file_path = self.base_directory / ".pdf2md_index.json"
        else:
            json_file_path = Path(json_file_path)

        try:
            if not json_file_path.exists():
                return "none"

            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Look for the file in the JSON structure
            if 'files' in data:
                for file_entry in data['files']:
                    if file_entry.get('name') == source_filename:
                        # Check if meta field exists and has content
                        meta = file_entry.get('meta')
                        if meta and isinstance(meta, dict) and len(meta) > 0:
                            return "exists"
                        else:
                            return "none"

            return "none"

        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            return "none"

    def get_metadata_values(self, source_filename: str, json_file_path: Optional[str] = None) -> Optional[dict]:
        """
        Get the actual metadata values for a specific source file from the JSON index.

        Args:
            source_filename: Name of the source file to check
            json_file_path: Optional path to JSON index file. If None, looks for .pdf2md_index.json

        Returns:
            Dictionary of metadata values or None if not found
        """
        if json_file_path is None:
            json_file_path = self.base_directory / ".pdf2md_index.json"
        else:
            json_file_path = Path(json_file_path)

        try:
            if not json_file_path.exists():
                return None

            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Look for the file in the JSON structure
            if 'files' in data:
                for file_entry in data['files']:
                    if file_entry.get('name') == source_filename:
                        meta = file_entry.get('meta')
                        if meta and isinstance(meta, dict) and len(meta) > 0:
                            return meta

            return None

        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            return None

    def get_available_parsers(self, source_filename: str) -> List[str]:
        """
        Get all available parsers (strukts) for a specific source file.

        Args:
            source_filename: Name of the source file

        Returns:
            List of parser names available for this file
        """
        source_path = Path(source_filename)
        basename = source_path.stem

        # Find all markdown files for this source file
        md_pattern = str(self.md_directory / f"{basename}.*.md")
        markdown_files = glob.glob(md_pattern)

        parsers = []
        for md_file in markdown_files:
            md_path = Path(md_file)
            parts = md_path.stem.split('.')

            if len(parts) >= 2:
                parser = parts[-1]  # Last part before .md
                if parser not in parsers:
                    parsers.append(parser)

        return sorted(parsers)

    def print_discovery_report(self) -> None:
        """Print a detailed report of discovered files and rankings."""
        mappings = self.discover_files()

        print("📁 File Discovery Report")
        print("=" * 60)
        print(f"Base Directory: {self.base_directory}")
        print(f"Markdown Directory: {self.md_directory}")
        print(f"Total Files Found: {len(mappings)}")
        print()

        for i, mapping in enumerate(mappings, 1):
            print(f"{i}. {mapping.source_file} ({mapping.source_type.upper()})")

            # Get available parsers (strukts)
            available_parsers = self.get_available_parsers(mapping.source_file)
            if available_parsers:
                parsers_str = ", ".join(available_parsers)
                print(
                    f"    🔧 Strukts({len(available_parsers)}): {parsers_str}")
            else:
                print("    🔧 Strukts(0): none")

            # Check metadata existence and show values
            meta_status = self.check_metadata_exists(mapping.source_file)
            if meta_status == "exists":
                metadata_values = self.get_metadata_values(mapping.source_file)
                if metadata_values:
                    # Format metadata as key: value pairs
                    meta_items = []
                    for key, value in metadata_values.items():
                        # Truncate long values for display
                        if isinstance(value, str) and len(value) > 30:
                            display_value = value[:27] + "..."
                        else:
                            display_value = str(value)
                        meta_items.append(f"{key}: {display_value}")

                    meta_str = ", ".join(meta_items)
                    print(f"    🏷️  Metadata: ✅ exists")
                    print(f"                {meta_str}")
                else:
                    print(f"    🏷️  Metadata: ✅ exists")
            else:
                print(f"    🏷️  Metadata: ❌ none")
            print()
