import argparse
import sys
from strukt2meta.commands import (
    GenerateCommand,
    InjectCommand,
    DiscoverCommand,
    AnalyzeCommand,
    BatchCommand,
    DirmetaCommand,
    ClearmetaCommand,
    UnlistCommand,
    KriterienCommand,
    OfsCommand
)


def main():
    # Pre-parse: allow optional leading basedir before the subcommand, e.g.:
    #   strukt2meta .klark0 ofs "Project" --mode kriterien --step meta
    # We detect if the first CLI arg is not a known subcommand and not an option,
    # then treat it as an OFS BASE_DIR and remove it before argparse processes subcommands.
    known_commands = {
        'generate', 'inject', 'discover', 'analyze', 'batch',
        'dirmeta', 'clearmeta', 'unlist', 'kriterien', 'ofs'
    }
    argv = sys.argv[1:]
    leading_basedir = None
    if argv and not argv[0].startswith('-') and argv[0] not in known_commands:
        # Consider first arg a candidate basedir
        leading_basedir = argv[0]
        argv = argv[1:]

    parser = argparse.ArgumentParser(
        description="""strukt2meta: AI-powered metadata generation and management.

This tool analyzes structured and unstructured text files (like Markdown)
to generate metadata using AI models. It can then inject this metadata
back into a structured JSON file system.

It offers a suite of commands for various operations:
""",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Add subcommands for different operations
    subparsers = parser.add_subparsers(
        dest='command',
        title='Available Commands',
        help='Run `strukt2meta <command> --help` for more information on a specific command.'
    )

    # Generate command
    generate_parser = subparsers.add_parser(
        'generate',
        help='Generate metadata from a single source file.',
        description='Reads a source file, applies an AI prompt, and saves the generated metadata to an output file.'
    )
    generate_parser.add_argument("--i", "--inpath", required=False, default="./default_input.md",
                                 help="Path to the input markdown source file (default: ./default_input.md)")
    generate_parser.add_argument("--p", "--prompt", default="zusammenfassung",
                                 help="Name of the prompt file (without .md) from the ./prompts directory (default: zusammenfassung)")
    generate_parser.add_argument("--o", "--outfile", required=True,
                                 help="Path to the output JSON file for the generated metadata")
    generate_parser.add_argument("--j", "--json-cleanup", action="store_true",
                                 help="Enable auto-repair for AI-generated JSON output")
    generate_parser.add_argument("-v", "--verbose", action="store_true",
                                 help="Enable verbose mode to stream the AI model's response")

    # Inject command
    inject_parser = subparsers.add_parser(
        'inject',
        help='Inject pre-generated metadata into a target JSON file.',
        description='Injects metadata from a source into a target JSON file based on a parameter configuration.'
    )
    inject_parser.add_argument("--params", "-p", required=True,
                               help="Path to the JSON file containing injection parameters")
    inject_parser.add_argument("--dry-run", "-d", action="store_true",
                               help="Perform a dry run without modifying any files")
    inject_parser.add_argument("-v", "--verbose", action="store_true",
                               help="Enable verbose output for detailed logging")

    # Discover command
    discover_parser = subparsers.add_parser(
        'discover',
        help='Discover and rank relevant source files in a directory.',
        description='Scans a directory to find and rank files based on their suitability as a data source for metadata generation.'
    )
    discover_parser.add_argument("--directory", "-d", required=True,
                                 help="Base directory to search for source files")
    discover_parser.add_argument("--config", "-c",
                                 help="Optional path to a custom parser ranking configuration file")
    discover_parser.add_argument("-v", "--verbose", action="store_true",
                                 help="Enable verbose output for detailed logging")

    # Analyze command
    analyze_parser = subparsers.add_parser(
        'analyze',
        help='Analyze a directory to find the best source file for metadata generation.',
        description='Automatically discovers and analyzes files to determine the best candidate for metadata extraction.'
    )
    analyze_parser.add_argument("--directory", "-d", required=True,
                                help="Base directory containing source files to analyze")
    analyze_parser.add_argument("--file", "-f",
                                help="Optional: Path to a specific source file to analyze directly")
    analyze_parser.add_argument("--prompt", "-p", default="metadata_extraction",
                                help="Prompt to use for the analysis (default: metadata_extraction)")
    analyze_parser.add_argument("--output", "-o",
                                help="Optional: Path to an output file to save the analysis results")
    analyze_parser.add_argument("--json-file", "-j",
                                help="Optional: Path to a JSON index file to check for existing metadata")
    analyze_parser.add_argument("--config", "-c",
                                help="Optional: Path to a custom parser ranking configuration file")
    analyze_parser.add_argument("-v", "--verbose", action="store_true",
                                help="Enable verbose output for detailed logging")

    # Batch command (DEPRECATED)
    batch_parser = subparsers.add_parser(
        'batch',
        help='[DEPRECATED] Batch process multiple source files and inject metadata into a JSON file.',
        description='[DEPRECATED] Use "dirmeta" instead. Intelligently discovers, analyzes, and processes multiple files to generate and inject metadata in a single run.'
    )
    batch_parser.add_argument("--directory", "-d", required=True,
                              help="Base directory containing the source files for batch processing")
    batch_parser.add_argument("--json-file", "-j", required=True,
                              help="Path to the target JSON file for metadata injection")
    batch_parser.add_argument("--prompt", "-p", default="metadata_extraction",
                              help="Prompt to use for metadata generation (default: metadata_extraction)")
    batch_parser.add_argument("--config", "-c",
                              help="Optional: Path to a custom parser ranking configuration file")
    batch_parser.add_argument("--dry-run", action="store_true",
                              help="Perform a dry run without modifying any files")
    batch_parser.add_argument("-v", "--verbose", action="store_true",
                              help="Enable verbose output for detailed logging")

    # Dirmeta command
    dirmeta_parser = subparsers.add_parser(
        'dirmeta',
        help='Automatically generate and inject metadata for all supported files in a directory.',
        description='Processes a directory to automatically analyze files, generate metadata, and inject it into a central JSON index file.'
    )
    dirmeta_parser.add_argument(
        '-d', '--directory',
        required=True,
        help='Path to the target directory to process'
    )
    dirmeta_parser.add_argument(
        '-p', '--prompt',
        required=True,
        help='Name of the prompt to use for analysis (e.g., lampen_metadata_extraction)'
    )
    dirmeta_parser.add_argument(
        '-j', '--json-file',
        help='Path to the JSON index file (default: <directory>/.ofs.index.json with legacy fallback .pdf2md_index.json)'
    )
    dirmeta_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output for detailed logging'
    )
    dirmeta_parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing metadata (by default, skips files with existing metadata)'
    )
    dirmeta_parser.add_argument(
        '--json-cleanup',
        action='store_true',
        help='Enable auto-repair for AI-generated JSON output'
    )

    # Clearmeta command
    clearmeta_parser = subparsers.add_parser(
        'clearmeta',
        help='Clear or remove specific metadata fields from a JSON file.',
        description='Removes specified metadata fields from a JSON file, either individually or all at once.'
    )
    clearmeta_parser.add_argument('json_file', help='Path to the JSON file to process')
    clearmeta_group = clearmeta_parser.add_mutually_exclusive_group(required=True)
    clearmeta_group.add_argument('--clean', dest='fields', help='Comma-separated list of top-level metadata fields to clear (e.g., "name,type")')
    clearmeta_group.add_argument('--all', action='store_true', help='Clear all top-level metadata fields')
    clearmeta_parser.add_argument('--dry-run', action='store_true', help='Show what would be cleared without making changes')
    clearmeta_parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output for detailed logging')
    clearmeta_parser.set_defaults(command_class=ClearmetaCommand)

    # Unlist command
    unlist_parser = subparsers.add_parser(
        'unlist',
        help='Process uncategorized files from <directory>/un_items.json.',
        description=(
            'Processes uncategorized files listed in "un_items.json" inside the given directory. '
            'Use --num to limit the number of files; by default all suitable files are processed.'
        )
    )
    unlist_parser.add_argument(
        'directory',
        help='Directory containing un_items.json and the referenced files'
    )
    unlist_parser.add_argument(
        '--num',
        type=int,
        default=None,
        help='Number of files to process (default: all)'
    )
    unlist_parser.add_argument(
        '--json-file',
        dest='json_file',
        help='Optional path to a custom JSON file containing the un_items array (defaults to <directory>/un_items.json)'
    )
    unlist_parser.add_argument(
        '-p', '--prompt',
        default='metadata_extraction',
        help='Name of the prompt to use for categorization (default: metadata_extraction)'
    )
    unlist_parser.add_argument(
        '-t', '--target-json',
        help='Optional: Target JSON file to inject generated metadata into'
    )
    unlist_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what files would be processed without actually processing them'
    )
    unlist_parser.add_argument(
        '--json-cleanup',
        action='store_true',
        help='Enable auto-repair for AI-generated JSON output'
    )
    unlist_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output for detailed logging'
    )

    # Kriterien command
    kriterien_parser = subparsers.add_parser(
        'kriterien',
        help='Extract criteria from tender documents (Ausschreibungsunterlagen).',
        description='Analyzes tender documents to extract criteria using AI models. Supports both overwrite and insert modes for JSON output.'
    )
    kriterien_parser.add_argument(
        '-p', '--prompt',
        required=True,
        help='Path to the prompt file for criteria extraction'
    )
    kriterien_parser.add_argument(
        '-f', '--file',
        required=True,
        help='Path to the tender document file to analyze'
    )
    kriterien_parser.add_argument(
        '-o', '--output',
        required=True,
        help='Path to the output JSON file'
    )
    kriterien_parser.add_argument(
        '-i', '--insert',
        type=str,
        help='Insert mode: specify JSON key to clear and replace (e.g., "meta", "kriterien")'
    )
    kriterien_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output for detailed logging'
    )

    # OFS command
    ofs_parser = subparsers.add_parser(
        'ofs',
        help='Process files in Opinionated File System (OFS) structure.',
        description='Processes files in OFS directory structure using projectname[@biddername][@filename] patterns. Supports autoprompt selection for A/adok and B/bdok directories.'
    )
    ofs_parser.add_argument(
        'ofs',
        help='OFS parameter: projectname[@biddername][@filename] - specify project, optional bidder, and optional filename'
    )
    ofs_parser.add_argument(
        '--mode',
        choices=['standard', 'kriterien'],
        default='standard',
        help='Processing mode: standard (default metadata extraction) or kriterien (criteria extraction)'
    )
    ofs_parser.add_argument(
        '--step',
        choices=['meta', 'bdoks', 'ids'],
        help='Kriterien step to execute (only used with --mode kriterien): meta, bdoks, or ids'
    )
    ofs_parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Process all files, including those that already have metadata (default: skip files with existing metadata)'
    )
    ofs_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output for detailed logging'
    )

    # Use our adjusted argv (potentially without the leading basedir)
    args = parser.parse_args(argv)

    # Apply leading basedir override for OFS-based commands
    if leading_basedir is not None and args.command in {'ofs', 'unlist'}:
        # Normalize to absolute path
        import os as _os
        from pathlib import Path as _Path
        base_dir = str(_Path(leading_basedir).expanduser().resolve())
        # Set environment variable so new OFS config instances pick it up
        _os.environ['OFS_BASE_DIR'] = base_dir
        # Also update the live OFS config singleton if available
        try:
            from ofs.config import get_config as _ofs_get_config
            _ofs_get_config().set('BASE_DIR', base_dir)
        except Exception:
            # If ofs isn't available or fails to import here, commands that need it will handle it
            pass

    if args.command is None:
        parser.print_help()
        return

    # Route to appropriate command handler
    command_handlers = {
        'generate': GenerateCommand,
        'inject': InjectCommand,
        'discover': DiscoverCommand,
        'analyze': AnalyzeCommand,
        'batch': BatchCommand,
        'dirmeta': DirmetaCommand,
        'clearmeta': ClearmetaCommand,
        'unlist': UnlistCommand,
        'kriterien': KriterienCommand,
        'ofs': OfsCommand
    }
    
    # Execute the appropriate command
    if args.command in command_handlers:
        handler_class = command_handlers[args.command]
        handler = handler_class(args)
        handler.validate_and_run()
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)






if __name__ == "__main__":
    main()
