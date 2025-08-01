# main.py - Main entry point for PDF to Markdown conversion

from pdf2md.config import config
from pdf2md.converter import PDFtoMarkdown
from pdf2md.factory import ExtractorFactory
from pdf2md.index import create_index, update_index, clear_index, get_index_data, print_index_stats, generate_unparsed_file_list, generate_un_items_list
import os
import argparse
import platform
import glob
import shutil
from typing import List, Optional
import time
import json
import hashlib
from datetime import datetime
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

                # Update index file after successful conversion
                index_file_path = os.path.join(input_dir, '.pdf2md_index.json')
                if not os.path.exists(index_file_path):
                    index_data = {"files": []}
                else:
                    with open(index_file_path, 'r') as index_file:
                        index_data = json.load(index_file)

                # Update or add file entry in the index
                file_entry = next((entry for entry in index_data["files"] if entry["name"] == file), None)
                if not file_entry:
                    file_entry = {"name": file, "parsers": {"det": []}}
                    index_data["files"].append(file_entry)

                if parser not in file_entry["parsers"]["det"]:
                    file_entry["parsers"]["det"].append(parser)

                with open(index_file_path, 'w') as index_file:
                    json.dump(index_data, index_file, indent=4)

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


def show_parsing_status(directory: str, recursive: bool, parser_name: Optional[str]):
    """Show the parsing status of files based on the index.

    Args:
        directory: The root directory to check.
        recursive: Whether to check subdirectories recursively.
        parser_name: The specific parser to check for. If None, checks for any parsing.
    """
    print(f"Checking parsing status in: {os.path.abspath(directory)}")
    if parser_name:
        print(f"Looking for files not parsed by: '{parser_name}'")
    else:
        print("Looking for files that have not been parsed by any parser.")
    print("-" * 20)

    unparsed_files_map = {}
    total_unparsed_count = 0
    start_directory = os.path.abspath(directory)

    for root, dirs, _ in os.walk(start_directory):
        # Modify dirs in-place to control traversal
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'md']

        index_data = get_index_data(root)

        if not index_data:
            print(f"[Warning] No index file found in: {root}. Skipping.")
            continue

        unparsed_in_dir = []
        for file_info in index_data.get('files', []):
            file_name = file_info['name']
            parsers_detected = file_info.get('parsers', {}).get('det', [])

            is_unparsed = False
            if parser_name:
                if parser_name not in parsers_detected:
                    is_unparsed = True
            else:
                if not parsers_detected:
                    is_unparsed = True

            if is_unparsed:
                unparsed_in_dir.append(file_name)

        if unparsed_in_dir:
            unparsed_files_map[root] = unparsed_in_dir
            total_unparsed_count += len(unparsed_in_dir)

        if not recursive:
            break  # Stop after the first level if not recursive

    # Print the results
    if not unparsed_files_map:
        print("\nAll relevant files seem to be parsed according to the criteria.")
    else:
        print(f"\nFound {total_unparsed_count} unparsed file(s):")
        for dir_path, files in unparsed_files_map.items():
            relative_dir_path = os.path.relpath(dir_path, start_directory)
            if relative_dir_path == '.':
                print(f"\nIn directory: {start_directory}")
            else:
                print(f"\nIn directory: {relative_dir_path}")

            for file_name in files:
                print(f"  - {file_name}")


def process_single_file(file_path: str, converter: PDFtoMarkdown, args) -> tuple[int, int]:
    """Process a single file with the given converter and arguments.

    Returns:
        Tuple of (processed_files_count, skipped_files_count)
    """
    # Get file details
    file_dir = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)
    base_name = os.path.splitext(file_name)[0]
    
    print(f"Processing single file: {file_name}")

    processed_files = 0
    skipped_files = 0

    # Validate file extension against each parser
    for parser in args.parsers:
        if parser not in converter.extractors:
            print(f"  Warning: Unknown parser '{parser}'. Skipping.")
            continue

        # Validate file extension against parser support
        if not ExtractorFactory.validate_file_extension(parser, file_path):
            supported_exts = ExtractorFactory.get_supported_extensions(parser)
            print(f"  Warning: {parser} extractor only supports {', '.join(supported_exts)} files. Skipping.")
            continue

        output_filename = f"{base_name}.{parser}.md"

        # For marker extractor, create a dedicated subdirectory structure
        if parser == 'marker':
            if not file_name.lower().endswith('.pdf'):
                print(f"  Warning: Marker extractor can only process PDF files. Skipping.")
                continue

            # Check if marker output directory already exists
            marker_output_dir = os.path.join(file_dir, 'md', base_name)
            if os.path.exists(marker_output_dir) and not args.overwrite:
                print(f"  Marker output directory already exists. Skipping conversion.")
                continue

            result = converter.convert(file_path, marker_output_dir, output_filename, parser, args.overwrite)
        else:
            result = converter.convert(file_path, os.path.join(file_dir, 'md'), output_filename, parser, args.overwrite)

        if result:
            processed_files += 1
            print(f"  ✓ Converted to {output_filename} using {parser}")

            # Update index file after successful conversion
            index_file_path = os.path.join(file_dir, '.pdf2md_index.json')
            if not os.path.exists(index_file_path):
                index_data = {"files": []}
            else:
                with open(index_file_path, 'r') as index_file:
                    index_data = json.load(index_file)

            # Update or add file entry in the index
            file_entry = next((entry for entry in index_data["files"] if entry["name"] == file_name), None)
            if not file_entry:
                file_entry = {"name": file_name, "parsers": {"det": []}}
                index_data["files"].append(file_entry)

            if parser not in file_entry["parsers"]["det"]:
                file_entry["parsers"]["det"].append(parser)

            with open(index_file_path, 'w') as index_file:
                json.dump(index_data, index_file, indent=4)

        else:
            skipped_files += 1

    print(f"\n[Single File: {file_name}] Processed: {processed_files}, Skipped: {skipped_files}")
    return processed_files, skipped_files


def main():
    """Main entry point for the PDF to Markdown converter."""
    # Get default input directory from config
    default_input = config.get_input_directory()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Convert PDF to Markdown\n\nInstallation:\n  pip install git+https://github.com/devskale/python-utils.git#subdirectory=packages/pdf2md.skale")
    parser.add_argument("--version", action="store_true",
                        help="Show version and exit")
    parser.add_argument("input_path", nargs='?', default=default_input,
                        help=f"Path to PDF file or directory containing PDF files (default: {default_input})")
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
    parser.add_argument("--index", choices=['create', 'update', 'clear', 'test', 'stats', 'un'],
                        help="Index operations: create new index, update existing, clear all indexes, test index update (dry run), print stats, or list unparsed and uncategorized items")
    parser.add_argument("-J", "--json", action="store_true",
                        help="Output the result in JSON format (used with --index un)")
    parser.add_argument("-o", "--output", type=str,
                        help="Specify the output file (used with --index un)")
    parser.add_argument("--index-age", type=int, default=30,
                        help="Maximum age (in seconds) for index files before they're considered stale (default: 30)")
    parser.add_argument("--status", nargs='?', const='all', default=None,
                        help="Show parsing status. Provide a parser name to see files not yet parsed by it. Without a name, it shows completely unparsed files.")
    args = parser.parse_args()

    if args.version:
        from pkg_resources import get_distribution
        version = get_distribution('pdf2md-skale').version
        print(f"pdf2md version {version}")
        return

    # Handle status check
    if args.status is not None:
        parser_to_check = None if args.status == 'all' else args.status
        input_path = args.input_path
        
        # For single files, use the parent directory for status check
        if os.path.isfile(input_path):
            input_path = os.path.dirname(input_path)
        
        show_parsing_status(input_path, args.recursive, parser_to_check)
        return

    # Handle index operations
    if args.index == 'create':
        input_path = args.input_path
        # For single files, use the parent directory for index operations
        if os.path.isfile(input_path):
            input_path = os.path.dirname(input_path)
        print(f"Creating new indexes in {input_path}")
        create_index(input_path, args.recursive)
        print("Index creation complete!")
        return
    elif args.index == 'update':
        input_path = args.input_path
        # For single files, use the parent directory for index operations
        if os.path.isfile(input_path):
            input_path = os.path.dirname(input_path)
        print(f"Updating indexes in {input_path} (max age: {args.index_age}s)")
        update_index(input_path, args.index_age, args.recursive, test_mode=False)
        print("Index update complete!")
        return
    elif args.index == 'test':
        input_path = args.input_path
        # For single files, use the parent directory for index operations
        if os.path.isfile(input_path):
            input_path = os.path.dirname(input_path)
        print(f"Testing index update in {input_path} (max age: {args.index_age}s) - NO CHANGES WILL BE SAVED")
        update_index(input_path, args.index_age, args.recursive, test_mode=True)
        print("Index test complete!")
        return
    elif args.index == 'clear':
        input_path = args.input_path
        # For single files, use the parent directory for index operations
        if os.path.isfile(input_path):
            input_path = os.path.dirname(input_path)
        print(f"Clearing indexes in {input_path}")
        clear_index(input_path, args.recursive)
        print("Index clearing complete!")
        return
    elif args.index == 'stats':
        input_path = args.input_path
        # For single files, use the parent directory for index operations
        if os.path.isfile(input_path):
            input_path = os.path.dirname(input_path)
        print(f"Showing stats for indexes in {input_path}")
        print_index_stats(input_path)
        return
    elif args.index == 'un':
        input_path = args.input_path
        # For single files, use the parent directory for index operations
        if os.path.isfile(input_path):
            input_path = os.path.dirname(input_path)
        print(f"Generating list of unparsed and uncategorized items in {input_path}")
        
        start_time = time.time()

        if args.json:
            output_file = args.output or os.path.join(input_path, "un_items.json")
        else:
            output_file = args.output or os.path.join(input_path, "un_items.txt")
        generate_un_items_list(input_path, output_file, args.recursive, args.json)

        end_time = time.time()
        processing_time = end_time - start_time

        # Ensure the file exists before opening it in 'r+' mode
        if not os.path.exists(output_file):
            with open(output_file, 'w') as f:
                json.dump({}, f)  # Initialize with an empty JSON object

        with open(output_file, 'r+') as f:
            data = json.load(f)
            data['processing_time'] = processing_time
            data['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

        print(f"Unparsed and uncategorized items list saved to: {output_file}")
        return

    if args.clear_parser:
        input_path = args.input_path
        # For single files, use the parent directory for clear operations
        if os.path.isfile(input_path):
            input_path = os.path.dirname(input_path)
        print(f"Clearing markdown files for parser: {args.clear_parser}")
        clear_parser_files(input_path, args.clear_parser, args.recursive)
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

    input_path = args.input_path

    if not os.path.exists(input_path):
        print(f"Error: The input path {input_path} does not exist.")
        return

    # Determine if input is a file or directory
    is_single_file = os.path.isfile(input_path)
    
    if is_single_file:
        # Validate file extension for single file input
        file_ext = os.path.splitext(input_path)[1].lower()
        valid_extensions = ['.pdf', '.docx', '.xlsx', '.pptx']
        
        if file_ext not in valid_extensions:
            print(f"Error: Unsupported file type '{file_ext}'. Supported types: {', '.join(valid_extensions)}")
            return
            
        # For single files, check parser compatibility
        compatible_parsers = []
        for parser in args.parsers:
            if ExtractorFactory.validate_file_extension(parser, input_path):
                compatible_parsers.append(parser)
        
        if not compatible_parsers:
            supported_by_parser = {}
            for parser in args.parsers:
                supported_by_parser[parser] = ExtractorFactory.get_supported_extensions(parser)
            
            print(f"Error: None of the specified parsers support '{file_ext}' files.")
            print("Parser compatibility:")
            for parser, exts in supported_by_parser.items():
                print(f"  {parser}: {', '.join(exts)}")
            return

    if args.dry:
        if is_single_file:
            print(f"Single file: {os.path.basename(input_path)}")
            print(f"Location: {os.path.dirname(input_path)}")
            print(f"Compatible parsers: {', '.join(compatible_parsers)}")
        else:
            print_directory_stats(input_path, args.recursive)
        return

    if is_single_file:
        print(f"\nProcessing single file: {os.path.abspath(input_path)}")
    else:
        print(f"\nProcessing files in: {os.path.abspath(input_path)}")
    
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

    if is_single_file:
        # Process single file
        process_single_file(input_path, converter, args)
    elif args.recursive:
        # Process directories recursively
        processed_files = 0
        processed_dirs = 0
        skipped_files = 0

        # First count total directories and files to process
        total_dirs = 0
        total_files_to_process = 0
        for root, dirs, files in os.walk(input_path):
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

        for root, dirs, files in os.walk(input_path):
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
        process_directory(input_path, converter, args)

    print("\n✓ Conversion complete!")


if __name__ == "__main__":
    main()
