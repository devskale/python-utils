# main.py - Main entry point for PDF to Markdown conversion

import os
import argparse
import platform
from typing import List, Optional

# Import local modules
from pdf2md.factory import ExtractorFactory
from pdf2md.converter import PDFtoMarkdown
from pdf2md.config import config


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
        'Other': 0
    }

    def process_dir(current_dir: str) -> None:
        """Process files in a single directory."""
        for item in os.listdir(current_dir):
            # Skip hidden files/directories and ./md subdirs
            if item.startswith('.') or item == 'md':
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
        'Other': 0,
        'Directories': 0
    }

    # Process root directory (show zero counts)
    root_counts = {'PDF': 0, 'Office': 0, 'Img': 0, 'Other': 0}
    print(f"[{os.path.basename(input_dir)}] Total {sum(root_counts.values())}")

    if recursive:
        # Process subdirectories
        for root, dirs, files in os.walk(input_dir):
            # Skip hidden directories and ./md subdirs
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'md']

            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                counts = count_files_by_type(dir_path, recursive=False)
                rel_path = os.path.relpath(dir_path, input_dir)

                # Format output to show full path with counts
                path_parts = os.path.join(os.path.basename(
                    input_dir), rel_path).split(os.sep)
                display_path = '/'.join(path_parts)

                print(
                    f"[{display_path}] Total:{sum(counts.values())} PDF:{counts['PDF']} Office:{counts['Office']} Img:{counts['Img']}")

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
                           if f.lower().endswith('.pdf')]
        if not supported_files:
            print(f"No PDF files found in {input_dir}")
            return (0, 0)
    else:
        if 'marker' in args.parsers:
            supported_files = [f for f in os.listdir(input_dir)
                               if f.lower().endswith('.pdf')]
        else:
            supported_files = [f for f in os.listdir(input_dir)
                               if f.lower().endswith(('.pdf', '.docx', '.xlsx', '.pptx'))]
        if not supported_files:
            print(
                f"No supported files (PDF/DOCX/XLSX/PPTX) found in {input_dir}")
            return (0, 0)

    print(f"Processing {len(supported_files)} file(s) in {input_dir}:")
    for i, file in enumerate(supported_files, 1):
        print(f"  {i}. {file}")
    print()

    processed_files = 0
    skipped_files = 0

    for file in supported_files:
        file_path = os.path.join(input_dir, file)
        base_name = os.path.splitext(file)[0]

        for parser in args.parsers:
            print(f"\nProcessing with {parser}: {file}")
            if parser not in converter.extractors:
                print(f"Warning: Unknown parser '{parser}'. Skipping.")
                continue

            output_filename = f"{base_name}.{parser}.md"

            # Validate file extension against parser support
            if not ExtractorFactory.validate_file_extension(parser, file_path):
                supported_exts = ExtractorFactory.get_supported_extensions(
                    parser)
                print(
                    f"Warning: {parser} extractor only supports {', '.join(supported_exts)} files. Skipping {file}")
                continue

            # For marker extractor, create a dedicated subdirectory structure only for PDF files
            if parser == 'marker':
                if not file.lower().endswith('.pdf'):
                    print(
                        f"Warning: Marker extractor can only process PDF files. Skipping {file}")
                    continue

                # Check if marker output directory already exists
                marker_output_dir = os.path.join(
                    input_dir, 'md', base_name)
                if os.path.exists(marker_output_dir) and not args.overwrite:
                    print(
                        f"Marker output directory {marker_output_dir} already exists. Skipping conversion.")
                    continue

                result = converter.convert(
                    file_path, marker_output_dir, output_filename, parser, args.overwrite)
            else:
                result = converter.convert(
                    file_path, os.path.join(input_dir, 'md'), output_filename, parser, args.overwrite)

            if result:
                processed_files += 1
                print(f"Converted {file} to {output_filename} using {parser}")
            else:
                skipped_files += 1

    print(f"\nDirectory summary for {os.path.basename(input_dir)}:")
    print(f"  Processed files: {processed_files}")
    print(f"  Skipped files: {skipped_files}")

    return processed_files, skipped_files


def main():
    """Main entry point for the PDF to Markdown converter."""
    # Get default input directory from config
    default_input = config.get_input_directory()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Convert PDF to Markdown\n\nInstallation:\n  pip install git+https://github.com/devskale/python-utils.git#subdirectory=packages/pdf2md.skale")
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
    args = parser.parse_args()

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

        # First count total directories to process
        total_dirs = 0
        for root, dirs, _ in os.walk(input_directory):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'md']
            total_dirs += len(dirs)

        for root, dirs, files in os.walk(input_directory):
            # Skip hidden directories and ./md subdirs
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'md']

            # Process current directory
            print(
                f"\nProcessing directory [{processed_dirs + 1}/{total_dirs}]: {root}")
            dir_processed, dir_skipped = process_directory(
                root, converter, args)
            processed_files += dir_processed
            skipped_files += dir_skipped
            processed_dirs += 1

        print(f"\nProcessed {processed_dirs} directories recursively.")
        print(f"Total files processed: {processed_files}")
        print(f"Total files skipped: {skipped_files}")
    else:
        # Process single directory
        process_directory(input_directory, converter, args)

    print("\nConversion complete!")


if __name__ == "__main__":
    main()
