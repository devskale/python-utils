#!/usr/bin/env python3
"""
Directory Metadata Processor (dirmeta)

This script automatically processes a directory to:
1. Check if files exist in the directory
2. Check if files already have metadata in the JSON index
3. For files without metadata, analyze them with a specified prompt
4. Inject the extracted metadata into the JSON index

Usage:
    python dirmeta.py -d <directory> -p <prompt_name> [-j <json_file>] [-v]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Add the strukt2meta package to the path
sys.path.insert(0, str(Path(__file__).parent))

from strukt2meta.file_discovery import FileDiscovery
from strukt2meta.main import load_prompt, query_ai_model
from strukt2meta.injector import inject_metadata_to_json


def check_directory_has_files(directory: Path) -> bool:
    """
    Check if directory contains any supported files (PDF, DOCX, XLSX).
    
    Args:
        directory: Path to the directory to check
        
    Returns:
        True if supported files are found, False otherwise
    """
    supported_extensions = ['.pdf', '.docx', '.xlsx']
    
    for ext in supported_extensions:
        if list(directory.glob(f'*{ext}')):
            return True
    
    return False


def process_directory_metadata(directory: str, prompt_name: str, json_file: str = None, verbose: bool = False, overwrite: bool = False) -> None:
    """
    Process all files in a directory for metadata extraction and injection.
    
    Args:
        directory: Path to the directory to process
        prompt_name: Name of the prompt to use for analysis
        json_file: Optional path to JSON index file
        verbose: Enable verbose output
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        print(f"❌ Error: Directory '{directory}' does not exist")
        return
    
    if not dir_path.is_dir():
        print(f"❌ Error: '{directory}' is not a directory")
        return
    
    print(f"🔍 Processing directory: {directory}")
    print("=" * 60)
    
    # Step 1: Check if directory has files
    if not check_directory_has_files(dir_path):
        print("📁 No supported files found in directory (PDF, DOCX, XLSX)")
        print("✅ Nothing to process. Exiting.")
        return
    
    # Initialize file discovery
    discovery = FileDiscovery(base_directory=directory)
    mappings = discovery.discover_files()
    
    if not mappings:
        print("📁 No files with markdown strukts found")
        print("✅ Nothing to process. Exiting.")
        return
    
    print(f"📄 Found {len(mappings)} files with strukts")
    
    # Step 2: Check which files need metadata processing
    files_to_process = []
    files_with_metadata = 0
    
    for mapping in mappings:
        meta_status = discovery.check_metadata_exists(mapping.source_file, json_file)
        if meta_status == "exists" and not overwrite:
            files_with_metadata += 1
            if verbose:
                print(f"✅ {mapping.source_file} - metadata exists")
        else:
            files_to_process.append(mapping)
            if meta_status == "exists" and overwrite:
                if verbose:
                    print(f"🔄 {mapping.source_file} - will overwrite existing metadata")
            else:
                if verbose:
                    print(f"❌ {mapping.source_file} - needs processing")
    
    if overwrite and files_to_process:
        overwrite_count = sum(1 for mapping in mappings if discovery.check_metadata_exists(mapping.source_file, json_file) == "exists")
        print(f"📊 Status: {files_with_metadata} files have metadata, {len(files_to_process)} need processing")
        if overwrite_count > 0:
            print(f"🔄 Overwrite mode: Will reprocess {overwrite_count} files with existing metadata")
    else:
        print(f"📊 Status: {files_with_metadata} files have metadata, {len(files_to_process)} need processing")
    
    if not files_to_process:
        if overwrite:
            print("✅ All files processed. Nothing more to process. Exiting.")
        else:
            print("✅ All files already have metadata. Nothing to process. Exiting.")
        return
    
    # Step 3: Process files without metadata
    print(f"\n🚀 Starting analysis and injection for {len(files_to_process)} files...")
    print("=" * 60)
    
    processed_count = 0
    error_count = 0
    
    for i, mapping in enumerate(files_to_process, 1):
        filename = mapping.source_file
        print(f"\n[{i}/{len(files_to_process)}] Processing: {filename}")
        
        try:
            # Step 3.1: Analyze file with prompt
            print(f"  🔍 Analyzing with prompt '{prompt_name}'...")
            
            # Get the best markdown file for this source file
            best_md = discovery.get_best_markdown_for_file(filename)
            
            if not best_md:
                print(f"  ❌ No markdown file found for: {filename}")
                error_count += 1
                continue
            
            # Read the markdown file (best_md is already the full path)
            md_path = Path(best_md)
            if not md_path.exists():
                print(f"  ❌ Markdown file not found: {md_path}")
                error_count += 1
                continue
                
            with open(md_path, 'r', encoding='utf-8') as f:
                input_text = f.read()
            
            # Load the prompt
            prompt = load_prompt(prompt_name)
            
            # Call AI model to get metadata
            result = query_ai_model(prompt, input_text, verbose=verbose, json_cleanup=True)
            
            if verbose:
                print(f"  📊 Analysis result type: {type(result)}")
            
            # Parse the result to extract metadata
            metadata = {}
            if isinstance(result, dict):
                # If result is already a dict, use it directly
                if 'meta' in result:
                    metadata = result['meta']
                else:
                    metadata = result
            elif isinstance(result, str):
                # Try to parse as JSON
                try:
                    parsed_result = json.loads(result)
                    if isinstance(parsed_result, dict):
                        if 'meta' in parsed_result:
                            metadata = parsed_result['meta']
                        else:
                            metadata = parsed_result
                    else:
                        metadata = {"analysis": parsed_result}
                except json.JSONDecodeError:
                    metadata = {"analysis": result}
            else:
                metadata = {"analysis": str(result)}
            
            if verbose:
                print(f"  📝 Extracted metadata: {metadata}")
            
            # Check if metadata was extracted
            if not metadata:
                print(f"  ⚠️  Warning: No metadata extracted from analysis")
                error_count += 1
                continue
            
            print(f"  ✅ Analysis complete - extracted {len(metadata)} metadata fields")
            
            # Step 3.2: Inject metadata into JSON
            print(f"  💉 Injecting metadata into JSON index...")
            
            # Determine JSON file path
            if json_file:
                json_path = json_file
            else:
                json_path = str(Path(directory) / ".pdf2md_index.json")
            
            # Inject metadata
            inject_metadata_to_json(
                source_filename=filename,
                metadata=metadata,
                json_file_path=json_path,
                base_directory=directory
            )
            
            print(f"  ✅ Metadata injected successfully")
            processed_count += 1
            
            # Small delay to avoid overwhelming the system
            time.sleep(0.5)
            
        except Exception as e:
            error_msg = str(e)
            
            # Check if it's a token limit error
            if "max_tokens must be at least 1" in error_msg or "got -" in error_msg:
                print(f"  ⚠️  Document too large for API limits, trying with smaller chunk...")
                
                # Try with a much smaller chunk of the document
                try:
                    # Take only the first 20KB of the document
                    truncated_input = input_text[:20000]
                    if len(input_text) > 20000:
                        truncated_input += "\n\n[... Document truncated due to size limits ...]"
                    
                    result = query_ai_model(prompt, truncated_input, verbose=False, json_cleanup=True)
                    
                    # Parse the result (same logic as above)
                    metadata = {}
                    if isinstance(result, dict):
                        if 'meta' in result:
                            metadata = result['meta']
                        else:
                            metadata = result
                    elif isinstance(result, str):
                        try:
                            parsed_result = json.loads(result)
                            if isinstance(parsed_result, dict):
                                if 'meta' in parsed_result:
                                    metadata = parsed_result['meta']
                                else:
                                    metadata = parsed_result
                            else:
                                metadata = {"analysis": parsed_result}
                        except json.JSONDecodeError:
                            metadata = {"analysis": result}
                    else:
                        metadata = {"analysis": str(result)}
                    
                    if metadata:
                        print(f"  ✅ Analysis complete with truncated document - extracted {len(metadata)} metadata fields")
                        
                        # Inject metadata
                        if json_file:
                            json_path = json_file
                        else:
                            json_path = str(Path(directory) / ".pdf2md_index.json")
                        
                        inject_metadata_to_json(
                            source_filename=filename,
                            metadata=metadata,
                            json_file_path=json_path,
                            base_directory=directory
                        )
                        
                        print(f"  ✅ Metadata injected successfully (from truncated document)")
                        processed_count += 1
                    else:
                        print(f"  ❌ No metadata extracted even with truncated document")
                        error_count += 1
                        
                except Exception as retry_error:
                    print(f"  ❌ Retry failed: {str(retry_error)}")
                    error_count += 1
            else:
                print(f"  ❌ Error processing {filename}: {error_msg}")
                error_count += 1
            continue
    
    # Final summary
    print(f"\n🎯 Processing Complete!")
    print("=" * 60)
    print(f"✅ Successfully processed: {processed_count} files")
    print(f"❌ Errors encountered: {error_count} files")
    print(f"📊 Total files with metadata: {files_with_metadata + processed_count}")
    
    if error_count == 0:
        print("🎉 All files processed successfully!")
    else:
        print(f"⚠️  {error_count} files had errors and may need manual review")


def main():
    """Main function to handle command line arguments and execute directory processing."""
    parser = argparse.ArgumentParser(
        description="Directory Metadata Processor - Automatically analyze and inject metadata for files in a directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dirmeta.py -d '.disk/2025-04 Lampen/A' -p lampen_metadata_extraction
  python dirmeta.py -d '/path/to/docs' -p metadata_extraction -j custom_index.json -v
  python dirmeta.py -d '.disk/2025-04 Lampen/A' -p lampen_metadata_extraction --overwrite -v
        """
    )
    
    parser.add_argument(
        '-d', '--directory',
        required=True,
        help='Directory to process for metadata extraction'
    )
    
    parser.add_argument(
        '-p', '--prompt',
        required=True,
        help='Prompt name to use for metadata extraction (e.g., lampen_metadata_extraction)'
    )
    
    parser.add_argument(
        '-j', '--json-file',
        help='Path to JSON index file (default: <directory>/.pdf2md_index.json)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing metadata for files that already have it'
    )
    
    args = parser.parse_args()
    
    try:
        process_directory_metadata(
            directory=args.directory,
            prompt_name=args.prompt,
            json_file=args.json_file,
            verbose=args.verbose,
            overwrite=args.overwrite
        )
    except KeyboardInterrupt:
        print("\n\n⏹️  Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()