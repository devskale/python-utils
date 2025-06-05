# main.py - Main entry point for PDF to Markdown conversion

from pdf2md.config import config
from pdf2md.converter import PDFtoMarkdown
from pdf2md.factory import ExtractorFactory
from pdf2md.index import create_index, update_index, clear_index
import os
import argparse
import platform
import glob
import shutil
from typing import List, Optional
import time
import json
import hashlib
# Import local modules


def count_files_by_type(directory: str, recursive: bool = False) -> dict:
    """Count files by type in a directory.

    Args:
        directory: Path to directory to scan
        recursive: Whether to scan subdirectories recursively

    Returns:
        Dictionary with counts for each file type
    """
    file_counts = {
        'PDF': 0,
        'Office': 0,
        'Img': 0,
        'Markdown': 0,
        'Other': 0
    }

    def process_dir(current_dir: str) -> None:
        """Process files in a single directory."""
        for item in os.listdir(current_dir):
            # Skip hidden files/directories, ./md subdirs, and files starting with '_'
            if item.startswith('.') or item.startswith('_'):
                continue

            item_path = os.path.join(current_dir, item)

            if os.path.isdir(item_path):
                if recursive:
                    process_dir(item_path)
                continue

            # Count by file type
            lower_item = item.lower()
            if lower_item.endswith('.pdf'):
                file_counts['PDF'] += 1
            elif any(lower_item.endswith(ext) for ext in ['.docx', '.xlsx', '.pptx']):
                file_counts['Office'] += 1
            elif any(lower_item.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                file_counts['Img'] += 1
            elif lower_item.endswith('.md'):
                file_counts['Markdown'] += 1
            else:
                file_counts['Other'] += 1

    process_dir(directory)
    return file_counts


def print_directory_stats(input_dir: str, recursive: bool = False) -> None:
    """Print directory statistics in the requested format."""
    if not os.path.exists(input_dir):
        print(f"Error: The input directory {input_dir} does not exist.")
        return

    total_counts = {
        'PDF': 0,
        'Office': 0,
        'Img': 0,
        'Markdown': 0,
        'Other': 0,
        'Directories': 0
    }

    # Process root directory
    root_counts = count_files_by_type(input_dir, recursive=False)
    print(f"[{os.path.basename(input_dir)}] Total:{sum(root_counts.values())} PDF:{root_counts['PDF']} Office:{root_counts['Office']} Img:{root_counts['Img']} Markdown:{root_counts['Markdown']}")

    # Add root counts to total_counts
    for key in root_counts:
        total_counts[key] += root_counts[key]

    if recursive:
        # Process subdirectories
        for root, dirs, files in os.walk(input_dir):
            # Skip hidden directories, ./md subdirs, and directories starting with '_'
            dirs[:] = [d for d in dirs if not d.startswith(
                '.') and not d.startswith('_')]

            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                counts = count_files_by_type(dir_path, recursive=False)
                rel_path = os.path.relpath(dir_path, input_dir)

                # Format output to show full path with counts
                path_parts = os.path.join(os.path.basename(
                    input_dir), rel_path).split(os.sep)
                display_path = '/'.join(path_parts)

                print(
                    f"[{display_path}] Total:{sum(counts.values())} PDF:{counts['PDF']} Office:{counts['Office']} Img:{counts['Img']} Markdown:{counts['Markdown']}")

                # Update totals
                for key in counts:
                    total_counts[key] += counts[key]
                total_counts['Directories'] += 1

    # Print total summary
    print("\nTotal Summary:")
    print("-------------")
    print(f"Directories: {total_counts['Directories']}")
    print(f"PDF: {total_counts['PDF']}")
    print(f"Office: {total_counts['Office']}")
    print(f"Images: {total_counts['Img']}")
    print(f"Markdown: {total_counts['Markdown']}")
    print(f"Other: {total_counts['Other']}")
    print(
        f"Total Files: {sum(total_counts.values()) - total_counts['Directories']}")


def process_directory(input_dir: str, converter: PDFtoMarkdown, args) -> tuple[int, int]:
    """Process a single directory with the given converter and arguments.

    Returns:
        Tuple of (processed_files_count, skipped_files_count)
    """
    # Filter files based on extractor type
    if all(parser not in ['docling', 'marker'] for parser in args.parsers):
        supported_files = [f for f in os.listdir(input_dir)
                           if not f.startswith('.') and not f.startswith('_') and f.lower().endswith('.pdf')]
        if not supported_files:
            print(f"No PDF files found in {input_dir}")
            return (0, 0)
    else:
        if 'marker' in args.parsers:
            supported_files = [f for f in os.listdir(input_dir)
                               if not f.startswith('.') and not f.startswith('_') and f.lower().endswith('.pdf')]
        else:
            supported_files = [f for f in os.listdir(input_dir)
                               if not f.startswith('.') and not f.startswith('_') and f.lower().endswith(('.pdf', '.docx', '.xlsx', '.pptx'))]
        if not supported_files:
            print(
                f"No supported files (PDF/DOCX/XLSX/PPTX) found in {input_dir}")
            return (0, 0)

    print(f"Found {len(supported_files)} file(s) in {input_dir}")

    processed_files = 0
    skipped_files = 0

    for file_idx, file in enumerate(supported_files, 1):
        file_path = os.path.join(input_dir, file)
        base_name = os.path.splitext(file)[0]

        print(f"\n[File {file_idx}/{len(supported_files)}] Processing: {file}")

        for parser in args.parsers:
            if parser not in converter.extractors:
                print(f"  Warning: Unknown parser '{parser}'. Skipping.")
                continue

            output_filename = f"{base_name}.{parser}.md"

            # Validate file extension against parser support
            if not ExtractorFactory.validate_file_extension(parser, file_path):
                supported_exts = ExtractorFactory.get_supported_extensions(
                    parser)
                print(
                    f"  Warning: {parser} extractor only supports {', '.join(supported_exts)} files. Skipping.")
                continue

            # For marker extractor, create a dedicated subdirectory structure only for PDF files
            if parser == 'marker':
                if not file.lower().endswith('.pdf'):
                    print(
                        f"  Warning: Marker extractor can only process PDF files. Skipping.")
                    continue

                # Check if marker output directory already exists
                marker_output_dir = os.path.join(
                    input_dir, 'md', base_name)
                if os.path.exists(marker_output_dir) and not args.overwrite:
                    print(
                        f"  Marker output directory already exists. Skipping conversion.")
                    continue

                result = converter.convert(
                    file_path, marker_output_dir, output_filename, parser, args.overwrite)
            else:
                result = converter.convert(
                    file_path, os.path.join(input_dir, 'md'), output_filename, parser, args.overwrite)

            if result:
                processed_files += 1
                print(f"  ✓ Converted to {output_filename} using {parser}")
            else:
                skipped_files += 1

    print(
        f"\n[Directory: {os.path.basename(input_dir)}] Processed: {processed_files}, Skipped: {skipped_files}")

    return processed_files, skipped_files


def clear_parser_files(directory: str, parser_name: Optional[str] = None, recursive: bool = False) -> None:
    """Recursively remove markdown files for a specific parser or all .md files if no parser specified.
    For Marker parser, also removes the nested 'md/{basename}' directories.

    Args:
        directory: Path to directory to scan
        parser_name: Name of parser to clear files for (None to clear all .md files)
        recursive: Whether to scan subdirectories recursively
    """
    def clear_dir(current_dir: str) -> None:
        """Clear files in a single directory."""
        # First check for md subdirectory
        md_dir = os.path.join(current_dir, 'md')
        if os.path.exists(md_dir):
            for item in os.listdir(md_dir):
                # Skip hidden files/directories and files starting with '_'
                if item.startswith('.') or item.startswith('_'):
                    continue

                item_path = os.path.join(md_dir, item)

                # Handle Marker's special directory structure
                if parser_name and parser_name.lower() == 'marker' and os.path.isdir(item_path):
                    # Remove all .marker.md files in the directory
                    for marker_file in glob.glob(os.path.join(item_path, '*.marker.md')):
                        try:
                            os.remove(marker_file)
                            print(f"Removed: {marker_file}")
                        except OSError as e:
                            print(f"Error removing {marker_file}: {e}")
                    # Remove the directory itself, regardless of its contents
                    try:
                        shutil.rmtree(item_path)
                        print(
                            f"Removed directory and its contents: {item_path}")
                    except OSError as e:
                        print(
                            f"Error removing directory {item_path} and its contents: {e}")
                    continue

                # Remove files matching the pattern
                if parser_name:
                    if item.lower().endswith(f'.{parser_name.lower()}.md'):
                        try:
                            os.remove(item_path)
                            print(f"Removed: {item_path}")
                        except OSError as e:
                            print(f"Error removing {item_path}: {e}")
                else:
                    if item.lower().endswith('.md'):
                        try:
                            os.remove(item_path)
                            print(f"Removed: {item_path}")
                        except OSError as e:
                            print(f"Error removing {item_path}: {e}")

        # Process regular files in current directory (for backward compatibility)
        for item in os.listdir(current_dir):
            # Skip hidden files/directories and files starting with '_'
            if item.startswith('.') or item.startswith('_'):
                continue

            item_path = os.path.join(current_dir, item)

            if os.path.isdir(item_path):
                if recursive:
                    clear_dir(item_path)
                continue

            # Remove files matching the pattern
            if parser_name:
                if item.lower().endswith(f'.{parser_name.lower()}.md'):
                    try:
                        os.remove(item_path)
                        print(f"Removed: {item_path}")
                    except OSError as e:
                        print(f"Error removing {item_path}: {e}")
            else:
                if item.lower().endswith('.md'):
                    try:
                        os.remove(item_path)
                        print(f"Removed: {item_path}")
                    except OSError as e:
                        print(f"Error removing {item_path}: {e}")

    clear_dir(directory)


def main():
    """Main entry point for the PDF to Markdown converter."""
    # Get default input directory from config
    default_input = config.get_input_directory()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Convert PDF to Markdown\n\nInstallation:\n  pip install git+https://github.com/devskale/python-utils.git#subdirectory=packages/pdf2md.skale")
    parser.add_argument("--version", action="store_true",
                        help="Show version and exit")
    parser.add_argument("input_directory", nargs='?', default=default_input,
                        help=f"Directory containing PDF files (default: {default_input})")
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite existing files")
    parser.add_argument("--ocr", action="store_true",
                        help="Use OCR for text extraction")
    parser.add_argument("--ocr-lang", default=config.get('ocr_language'),
                        help=f"Language for OCR (default: {config.get('ocr_language')})")

    # Get available extractors from factory
    available_extractors = ExtractorFactory.get_available_extractors()
    default_parser = config.get('default_parser')

    parser.add_argument("--parsers", nargs='+', default=[default_parser],
                        help=f"List of parsers to use (available: {', '.join(available_extractors)}; default: {default_parser})")
    parser.add_argument("--recursive", action="store_true",
                        help="Process directories recursively")
    parser.add_argument("--dry", action="store_true",
                        help="Dry run - show file counts without conversion")
    parser.add_argument("--update", action="store_true",
                        help="Update pdf2md to the latest version from GitHub")
    parser.add_argument("--clear-parser",
                        help="Clear markdown files for a specific parser (e.g. 'marker')")
    parser.add_argument("--index", choices=['create', 'update', 'clear', 'test'],
                        help="Index operations: create new index, update existing, clear all indexes, or test index update (dry run)")
    parser.add_argument("--index-age", type=int, default=30,
                        help="Maximum age (in seconds) for index files before they're considered stale (default: 5)")
    args = parser.parse_args()

    if args.version:
        from pkg_resources import get_distribution
        version = get_distribution('pdf2md-skale').version
        print(f"pdf2md version {version}")
        return

    # Handle index operations
    if args.index == 'create':
        print(f"Creating new indexes in {args.input_directory}")
        create_index(args.input_directory, args.recursive)
        print("Index creation complete!")
        return
    elif args.index == 'update':
        print(
            f"Updating indexes in {args.input_directory} (max age: {args.index_age}s)")
        update_index(args.input_directory, args.index_age,
                     args.recursive, test_mode=False)
        print("Index update complete!")
        return
    elif args.index == 'test':
        print(
            f"Testing index update in {args.input_directory} (max age: {args.index_age}s) - NO CHANGES WILL BE SAVED")
        update_index(args.input_directory, args.index_age,
                     args.recursive, test_mode=True)
        print("Index test complete!")
        return
    elif args.index == 'clear':
        print(f"Clearing indexes in {args.input_directory}")
        clear_index(args.input_directory, args.recursive)
        print("Index clearing complete!")
        return

    if args.clear_parser:
        print(f"Clearing markdown files for parser: {args.clear_parser}")
        clear_parser_files(args.input_directory,
                           args.clear_parser, args.recursive)
        print("Clear operation complete!")
        return

    if args.update:
        print("Updating pdf2md from GitHub...")
        try:
            import subprocess
            subprocess.run(["pip", "install", "--upgrade",
                           "git+https://github.com/devskale/python-utils.git#subdirectory=packages/pdf2md.skale"], check=True)
            print("Update successful!")
            return
        except subprocess.CalledProcessError as e:
            print(f"Update failed: {e}")
            return

    input_directory = args.input_directory

    if not os.path.exists(input_directory):
        print(f"Error: The input directory {input_directory} does not exist.")
        return

    if args.dry:
        print_directory_stats(input_directory, args.recursive)
        return

    print(f"\nProcessing files in: {os.path.abspath(input_directory)}")
    print(f"Using parsers: {', '.join(args.parsers)}")
    print(f"Overwrite existing files: {'Yes' if args.overwrite else 'No'}")
    print(f"OCR enabled: {'Yes' if args.ocr else 'No'}")
    if args.ocr:
        print(f"OCR language: {args.ocr_lang}")
    print()

    # Check for PaddleOCR on macOS before initializing converter
    if 'paddleocr' in args.parsers and platform.system() == 'Darwin':
        print("Error: PaddleOCR is not supported on macOS. Please use one of these alternatives:")
        print("- OCRExtractor (pytesseract based): '--parsers ocr'")
        print("- EasyOCRExtractor (easyocr based): '--parsers easyocr'")
        return

    # Initialize converter with specified parsers
    converter = PDFtoMarkdown(args.parsers)

    # If OCR is requested, update the OCR extractor with the specified language
    if args.ocr and 'ocr' in converter.extractors:
        converter.update_ocr_extractor(args.ocr_lang)

    if args.recursive:
        # Process directories recursively
        processed_files = 0
        processed_dirs = 0
        skipped_files = 0

        # First count total directories and files to process
        total_dirs = 0
        total_files_to_process = 0
        for root, dirs, files in os.walk(input_directory):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            total_dirs += len(dirs)

            # Count files that would be processed
            if all(parser not in ['docling', 'marker'] for parser in args.parsers):
                total_files_to_process += sum(
                    1 for f in files if f.lower().endswith('.pdf'))
            else:
                if 'marker' in args.parsers:
                    total_files_to_process += sum(
                        1 for f in files if f.lower().endswith('.pdf'))
                else:
                    total_files_to_process += sum(1 for f in files if f.lower().endswith(
                        ('.pdf', '.docx', '.xlsx', '.pptx')))

        print(
            f"Found {total_dirs + 1} directories and {total_files_to_process} processable files")
        print("Starting conversion...\n")

        for root, dirs, files in os.walk(input_directory):
            # Skip hidden directories, ./md subdirs, and directories starting with '_'
            dirs[:] = [d for d in dirs if not d.startswith(
                '.') and not d.startswith('_')]

            # Process current directory
            print(
                f"\n[Directory {processed_dirs + 1}/{total_dirs + 1}] Processing: {root}")
            dir_processed, dir_skipped = process_directory(
                root, converter, args)
            processed_files += dir_processed
            skipped_files += dir_skipped
            processed_dirs += 1

            # Show overall progress with percentage
            if total_files_to_process > 0:
                progress_percent = round(
                    (processed_files + skipped_files) / total_files_to_process * 100)
                print(
                    f"Overall progress: {progress_percent}% [{processed_files + skipped_files}/{total_files_to_process}] (✓ {processed_files} processed, ✗ {skipped_files} skipped)")

        print(
            f"\n=== FINAL SUMMARY ===\nDirectories: {processed_dirs}/{total_dirs + 1} completed ({round(processed_dirs/(total_dirs + 1)*100)}%)\nFiles: {processed_files} processed, {skipped_files} skipped, {processed_files + skipped_files} total")
    else:
        # Process single directory
        process_directory(input_directory, converter, args)

    print("\n✓ Conversion complete!")


if __name__ == "__main__":
    main()
