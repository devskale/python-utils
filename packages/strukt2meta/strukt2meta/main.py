import argparse
import json
import os
from strukt2meta.apicall import call_ai_model

# Replace the placeholder function


def query_ai_model(prompt, input_text, verbose=False, json_cleanup=False):
    return call_ai_model(prompt, input_text, verbose, json_cleanup)


def load_prompt(prompt_name):
    prompts_dir = "./prompts"
    prompt_path = os.path.join(prompts_dir, f"{prompt_name}.md")
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    with open(prompt_path, "r") as prompt_file:
        return prompt_file.read()


def main():
    parser = argparse.ArgumentParser(
        description="Process a strukt file and generate JSON metadata.")

    # Add subcommands for different operations
    subparsers = parser.add_subparsers(
        dest='command', help='Available commands')

    # Generate command (original functionality)
    generate_parser = subparsers.add_parser(
        'generate', help='Generate metadata from strukt file')
    generate_parser.add_argument("--i", "--inpath", required=False, default="./default_input.md",
                                 help="Path to the input markdown strukt file (default: ./default_input.md)")
    generate_parser.add_argument("--p", "--prompt", default="zusammenfassung",
                                 help="Prompt file name (without .md) to use from the ./prompts directory (default: zusammenfassung)")
    generate_parser.add_argument("--o", "--outfile", required=True,
                                 help="Path to the output JSON file")
    generate_parser.add_argument("--j", "--json-cleanup", action="store_true",
                                 help="Enable JSON cleanup to repair and clean AI-generated JSON output")
    generate_parser.add_argument("-v", "--verbose", action="store_true",
                                 help="Enable verbose mode to stream API call response.")

    # Inject command (new functionality)
    inject_parser = subparsers.add_parser(
        'inject', help='Inject metadata into JSON file')
    inject_parser.add_argument("--params", "-p", required=True,
                               help="Path to the parameter configuration JSON file")
    inject_parser.add_argument("--dry-run", "-d", action="store_true",
                               help="Perform a dry run without actually modifying files")
    inject_parser.add_argument("-v", "--verbose", action="store_true",
                               help="Enable verbose output")

    # Discover command (file discovery)
    discover_parser = subparsers.add_parser(
        'discover', help='Discover files and show parser rankings')
    discover_parser.add_argument("--directory", "-d", required=True,
                                 help="Base directory to search for files")
    discover_parser.add_argument("--config", "-c",
                                 help="Optional configuration file for custom parser rankings")
    discover_parser.add_argument("-v", "--verbose", action="store_true",
                                 help="Enable verbose output")

    # Analyze command (intelligent analysis)
    analyze_parser = subparsers.add_parser(
        'analyze', help='Auto-discover and analyze best markdown files')
    analyze_parser.add_argument("--directory", "-d", required=True,
                                help="Base directory containing source files")
    analyze_parser.add_argument("--file", "-f",
                                help="Specific source file to analyze (optional)")
    analyze_parser.add_argument("--prompt", "-p", default="metadata_extraction",
                                help="Prompt to use for analysis")
    analyze_parser.add_argument("--output", "-o",
                                help="Output file for results (optional)")
    analyze_parser.add_argument("--json-file", "-j",
                                help="JSON index file to check for existing metadata (optional)")
    analyze_parser.add_argument("--config", "-c",
                                help="Configuration file for parser rankings")
    analyze_parser.add_argument("-v", "--verbose", action="store_true",
                                help="Enable verbose output")

    # Batch command (intelligent batch processing)
    batch_parser = subparsers.add_parser(
        'batch', help='Process multiple files with intelligent selection')
    batch_parser.add_argument("--directory", "-d", required=True,
                              help="Base directory containing source files")
    batch_parser.add_argument("--json-file", "-j", required=True,
                              help="Target JSON file for metadata injection")
    batch_parser.add_argument("--prompt", "-p", default="metadata_extraction",
                              help="Prompt to use for analysis")
    batch_parser.add_argument("--config", "-c",
                              help="Configuration file for parser rankings")
    batch_parser.add_argument("--dry-run", action="store_true",
                              help="Perform a dry run without modifying files")
    batch_parser.add_argument("-v", "--verbose", action="store_true",
                              help="Enable verbose output")

    # Dirmeta command (directory metadata processor - consolidated from dirmeta.py)
    dirmeta_parser = subparsers.add_parser(
        'dirmeta', help='Directory Metadata Processor - Automatically analyze and inject metadata for files in a directory')
    dirmeta_parser.add_argument(
        '-d', '--directory',
        required=True,
        help='Path to the directory to process'
    )
    dirmeta_parser.add_argument(
        '-p', '--prompt',
        required=True,
        help='Name of the prompt to use for analysis (e.g., lampen_metadata_extraction)'
    )
    dirmeta_parser.add_argument(
        '-j', '--json-file',
        help='Path to the JSON index file (default: <directory>/.pdf2md_index.json)'
    )
    dirmeta_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    dirmeta_parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing metadata (default: skip files with existing metadata)'
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if args.command == 'generate':
        handle_generate_command(args)
    elif args.command == 'inject':
        handle_inject_command(args)
    elif args.command == 'discover':
        handle_discover_command(args)
    elif args.command == 'analyze':
        handle_analyze_command(args)
    elif args.command == 'batch':
        handle_batch_command(args)
    elif args.command == 'dirmeta':
        handle_dirmeta_command(args)


def handle_generate_command(args):
    """Handle the generate command (original functionality)."""
    # Read the input file
    with open(args.i, "r") as infile:
        input_text = infile.read()
        print(f"Input text loaded from: {args.i}")

    # Load the prompt
    prompt = load_prompt(args.p)
    print(f"Using prompt: {args.p}")

    # Query the AI model
    result = query_ai_model(
        prompt, input_text, verbose=args.verbose, json_cleanup=args.j)

    # Write the result to the output file
    with open(args.o, "w") as outfile:
        json.dump(result, outfile, indent=4)
        print(f"Output written to: {args.o}")


def handle_inject_command(args):
    """Handle the inject command (new functionality)."""
    from strukt2meta.injector import JSONInjector

    try:
        if args.verbose:
            print(f"Loading parameters from: {args.params}")

        injector = JSONInjector(args.params)

        if args.dry_run:
            print("DRY RUN MODE - No files will be modified")
            print("Parameter validation: PASSED")
            print(f"Target file: {injector.params['target_filename']}")
            print(f"JSON file: {injector.params['json_inject_file']}")
            print(f"Input path: {injector.params['input_path']}")
            print(f"Prompt: {injector.params['prompt']}")
            return

        # Execute injection
        result = injector.inject()

        if result['success']:
            print("✅ Injection completed successfully!")
            if args.verbose:
                print(f"Target file: {result['target_file']}")
                print(f"Backup created: {result['backup_path']}")
                print("Injected metadata:")
                print(json.dumps(
                    result['injected_metadata'], indent=2, ensure_ascii=False))
        else:
            print("❌ Injection failed")

    except Exception as e:
        print(f"❌ Error during injection: {e}")
        raise


def handle_discover_command(args):
    """Handle the discover command for file discovery."""
    from strukt2meta.file_discovery import FileDiscovery

    try:
        if args.verbose:
            print(f"🔍 Discovering files in: {args.directory}")

        discovery = FileDiscovery(args.directory, args.config)
        discovery.print_discovery_report()

    except Exception as e:
        print(f"❌ Error during file discovery: {e}")
        raise


def handle_analyze_command(args):
    """Handle the analyze command for intelligent analysis."""
    from strukt2meta.file_discovery import FileDiscovery

    try:
        discovery = FileDiscovery(args.directory, args.config)

        if args.file:
            # Analyze specific file
            best_md = discovery.get_best_markdown_for_file(args.file)
            if not best_md:
                print(f"❌ No markdown file found for: {args.file}")
                return

            # Check if metadata already exists
            meta_status = discovery.check_metadata_exists(
                args.file, args.json_file)

            if args.verbose:
                print(f"📄 Analyzing: {args.file}")
                print(f"📝 Using markdown: {best_md}")
                print(f"🏷️  Metadata status: {meta_status}")

            # Read and analyze the markdown file
            with open(best_md, "r") as f:
                input_text = f.read()

            prompt = load_prompt(args.prompt)
            result = query_ai_model(prompt, input_text, verbose=args.verbose)

            # Add metadata existence status to the result
            if isinstance(result, dict):
                result["meta_status"] = meta_status
            elif isinstance(result, str):
                # If result is a string, try to parse as JSON and add the field
                try:
                    parsed_result = json.loads(result)
                    if isinstance(parsed_result, dict):
                        parsed_result["meta_status"] = meta_status
                        result = json.dumps(
                            parsed_result, indent=2, ensure_ascii=False)
                    else:
                        # If not a dict, create a wrapper
                        result = {
                            "analysis": result,
                            "meta_status": meta_status
                        }
                except json.JSONDecodeError:
                    # If parsing fails, create a wrapper
                    result = {
                        "analysis": result,
                        "meta_status": meta_status
                    }

            if args.output:
                with open(args.output, "w") as f:
                    if isinstance(result, str):
                        f.write(result)
                    else:
                        json.dump(result, f, indent=4, ensure_ascii=False)
                print(f"✅ Results written to: {args.output}")
            else:
                print("📊 Analysis Results:")
                if isinstance(result, str):
                    print(result)
                else:
                    print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            # Show available files for analysis
            mappings = discovery.discover_files()
            print(f"📁 Found {len(mappings)} files available for analysis:")
            for mapping in mappings:
                status = "✅" if mapping.best_markdown else "❌"
                meta_status = discovery.check_metadata_exists(
                    mapping.source_file)
                meta_icon = "🏷️" if meta_status == "exists" else "📝"
                print(
                    f"   {status} {mapping.source_file} ({mapping.source_type}) {meta_icon} meta: {meta_status}")
                if mapping.best_markdown:
                    print(
                        f"      → {mapping.best_markdown} (confidence: {mapping.confidence_score:.2f})")

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        raise


def handle_batch_command(args):
    """Handle the batch command for intelligent batch processing."""
    from strukt2meta.file_discovery import FileDiscovery
    from strukt2meta.injector import JSONInjector
    import tempfile

    try:
        discovery = FileDiscovery(args.directory, args.config)
        mappings = discovery.discover_files()

        if not mappings:
            print("❌ No files found for processing")
            return

        # Filter mappings to only include those with good markdown files
        valid_mappings = [
            m for m in mappings if m.best_markdown and m.confidence_score > 0.3]

        if args.verbose:
            print(f"📁 Found {len(mappings)} total files")
            print(f"✅ {len(valid_mappings)} files have suitable markdown")

        if args.dry_run:
            print("🔍 DRY RUN - Files that would be processed:")
            for mapping in valid_mappings:
                print(f"   📄 {mapping.source_file}")
                print(
                    f"      → {mapping.best_markdown} ({mapping.parser_used})")
            return

        # Ask for confirmation
        print(f"\n🚀 Process {len(valid_mappings)} files? (y/N): ", end="")
        if input().strip().lower() != 'y':
            print("⏹️ Batch processing cancelled")
            return

        # Process files
        successful = 0
        failed = 0

        for i, mapping in enumerate(valid_mappings, 1):
            print(
                f"\n🔄 Processing {i}/{len(valid_mappings)}: {mapping.source_file}")

            try:
                # Create temporary parameter file
                md_path = str(discovery.md_directory / mapping.best_markdown)

                params = {
                    "input_path": md_path,
                    "prompt": args.prompt,
                    "json_inject_file": args.json_file,
                    "target_filename": mapping.source_file,
                    "injection_schema": {
                        "meta": {
                            "kategorie": {"ai_generated_field": True},
                            "name": {"ai_generated_field": True},
                            "dokumenttyp": {"ai_generated_field": True},
                            "thema": {"ai_generated_field": True},
                            "sprache": {"ai_generated_field": True}
                        }
                    },
                    "backup_enabled": True
                }

                # Create temporary parameter file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(params, f, indent=2, ensure_ascii=False)
                    temp_param_file = f.name

                try:
                    # Process with injector
                    injector = JSONInjector(temp_param_file)
                    result = injector.inject()

                    if result['success']:
                        print(f"   ✅ Success: {mapping.source_file}")
                        successful += 1
                    else:
                        print(f"   ❌ Failed: {mapping.source_file}")
                        failed += 1

                finally:
                    # Clean up temp file
                    os.unlink(temp_param_file)

            except Exception as e:
                print(f"   ❌ Error: {mapping.source_file} - {str(e)}")
                failed += 1

        # Summary
        print(f"\n📊 Batch Processing Complete:")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📁 Total: {len(valid_mappings)}")

    except Exception as e:
        print(f"❌ Error during batch processing: {e}")
        raise


def handle_dirmeta_command(args):
    """Handle the dirmeta command for directory metadata processing (consolidated from dirmeta.py)."""
    from strukt2meta.file_discovery import FileDiscovery
    from strukt2meta.injector import inject_metadata_to_json
    from pathlib import Path
    import time
    import json

    def check_directory_has_files(dir_path):
        """Check if directory contains supported files (PDF, DOCX, XLSX)."""
        supported_extensions = ['.pdf', '.docx', '.xlsx']
        for ext in supported_extensions:
            if list(dir_path.glob(f'**/*{ext}')):
                return True
        return False

    directory = args.directory
    prompt_name = args.prompt
    json_file = args.json_file
    verbose = args.verbose
    overwrite = args.overwrite

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


if __name__ == "__main__":
    main()
