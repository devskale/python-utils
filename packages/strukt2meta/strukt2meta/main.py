import argparse
from strukt2meta.commands import (
    GenerateCommand,
    InjectCommand,
    DiscoverCommand,
    AnalyzeCommand,
    BatchCommand,
    DirmetaCommand
)


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

    # Route to appropriate command handler
    command_handlers = {
        'generate': GenerateCommand,
        'inject': InjectCommand,
        'discover': DiscoverCommand,
        'analyze': AnalyzeCommand,
        'batch': BatchCommand,
        'dirmeta': DirmetaCommand
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
