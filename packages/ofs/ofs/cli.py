"""Command Line Interface for OFS (Opinionated Filesystem).

Provides command-line access to OFS functionality.
"""

from .index import (
    create_index,
    update_index,
    clear_index,
    print_index_stats
)
from .core import (
    get_path,
    get_ofs_root,
    list_ofs_items,
    find_bidder_in_project,
    list_projects,
    list_bidders,
    get_paths_json,
    list_projects_json,
    list_bidders_json,
    list_bidder_docs_json,
    list_project_docs_json,
    get_bidder_document_json,
    get_project_document_json,
    print_tree_structure,
    generate_tree_structure,
    read_doc,
    get_kriterien_pop_json,
    get_kriterien_tree_json,
    get_kriterien_tag_json
)
import sys
import json
import argparse
from typing import Optional
from .logging import setup_logger

# Module logger
logger = setup_logger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for the OFS CLI.

    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        prog="ofs",
        description="OFS (Opinionated Filesystem) - Access and manage tender documentation",
        epilog="For more information, see the documentation."
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )

    subparsers = parser.add_subparsers(
        dest="command", help="Available commands")

    # get-path command
    get_path_parser = subparsers.add_parser(
        "get-path",
        help="Get the path for a given name (AUSSCHREIBUNGNAME or BIETERNAME)"
    )
    get_path_parser.add_argument(
        "name",
        help="Name to resolve to a path (project or bidder name)"
    )

    # list command
    list_parser = subparsers.add_parser(
        "list",
        help="List all available items in the OFS"
    )

    # list-projects command
    list_projects_parser = subparsers.add_parser(
        "list-projects",
        help="List all project names (AUSSCHREIBUNGNAME)"
    )

    # list-bidders command
    list_bidders_parser = subparsers.add_parser(
        "list-bidders",
        help="List all bidder names (BIETERNAME) in a project"
    )
    list_bidders_parser.add_argument(
        "project",
        help="Project name to list bidders for"
    )

    # find-bidder command
    find_bidder_parser = subparsers.add_parser(
        "find-bidder",
        help="Find a specific bidder within a project"
    )
    find_bidder_parser.add_argument(
        "project",
        help="Project name (AUSSCHREIBUNGNAME)"
    )
    find_bidder_parser.add_argument(
        "bidder",
        help="Bidder name (BIETERNAME)"
    )

    # list-docs command
    list_docs_parser = subparsers.add_parser(
        "list-docs",
        help="List documents (default: name + basic metadata)"
    )
    list_docs_parser.add_argument(
        "project_bidder",
        help="Project name, 'project@bidder', or 'project@bidder@filename' format"
    )
    list_docs_parser.add_argument(
        "--meta",
        action="store_true",
        help="Include full document details and metadata"
    )

    # root command
    root_parser = subparsers.add_parser(
        "root",
        help="Show the OFS root directory"
    )

    # tree command
    tree_parser = subparsers.add_parser(
        "tree",
        help="Show tree structure of projects, bidders, and documents"
    )
    tree_parser.add_argument(
        "-d", "--directories",
        action="store_true",
        help="Show only directory tree (no documents)"
    )

    # read-doc command
    read_doc_parser = subparsers.add_parser(
        "read-doc",
        help="Read a document by identifier 'Project@Filename' or 'Project@Bidder@Filename'"
    )
    read_doc_parser.add_argument(
        "identifier",
        help="Identifier in the form 'Project@Filename' (tender docs) or 'Project@Bidder@Filename' (bidder docs)"
    )
    read_doc_parser.add_argument(
        "--parser",
        dest="parser",
        default=None,
        help="Optional parser to use (docling, marker, llamaparse, pdfplumber). If omitted, uses ranked selection"
    )
    read_doc_parser.add_argument(
        "--json",
        action="store_true",
        help="Output full JSON result instead of just content"
    )

    # kriterien command
    kriterien_parser = subparsers.add_parser(
        "kriterien",
        help="Analyze criteria from JSON files for a project"
    )
    kriterien_parser.add_argument(
        "project",
        help="Project name (AUSSCHREIBUNGNAME)"
    )
    kriterien_subparsers = kriterien_parser.add_subparsers(
        dest="kriterien_action",
        help="Kriterien analysis actions"
    )

    # kriterien pop command
    pop_parser = kriterien_subparsers.add_parser(
        "pop",
        help="Show next unproven criteria"
    )
    pop_parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="Number of criteria to show (default: 1)"
    )

    # kriterien tree command
    tree_parser = kriterien_subparsers.add_parser(
        "tree",
        help="Show criteria tree organized by typ and kategorie"
    )

    # kriterien tag command
    tag_parser = kriterien_subparsers.add_parser(
        "tag",
        help="Show criterion by tag ID or list all tags"
    )
    tag_parser.add_argument(
        "tag_id",
        nargs="?",
        help="Specific tag ID to show (e.g., F_SUB_001). If omitted, shows all available tags"
    )

    # index command
    index_parser = subparsers.add_parser(
        "index",
        help="Manage OFS index files for faster access"
    )
    index_subparsers = index_parser.add_subparsers(
        dest="index_action",
        help="Index management actions"
    )

    # index create command
    create_parser = index_subparsers.add_parser(
        "create",
        help="Create index files for directories"
    )
    create_parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to index (default: current directory)"
    )
    create_parser.add_argument(
        "--recursive",
        action="store_true",
        help="Create indexes recursively for subdirectories"
    )
    create_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing index files"
    )

    # index update command
    update_parser = index_subparsers.add_parser(
        "update",
        help="Update existing index files"
    )
    update_parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to update indexes for (default: current directory)"
    )
    update_parser.add_argument(
        "--recursive",
        action="store_true",
        help="Update indexes recursively for subdirectories"
    )
    update_parser.add_argument(
        "--max-age",
        type=int,
        default=24,
        help="Maximum age in hours before forcing update (default: 24)"
    )

    # index clear command
    clear_parser = index_subparsers.add_parser(
        "clear",
        help="Remove index files from directories"
    )
    clear_parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to clear indexes from (default: current directory)"
    )
    clear_parser.add_argument(
        "--recursive",
        action="store_true",
        help="Clear indexes recursively from subdirectories"
    )

    # index stats command
    stats_parser = index_subparsers.add_parser(
        "stats",
        help="Show statistics for indexed files and directories"
    )
    stats_parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to analyze (default: current directory)"
    )

    # index un command
    un_parser = index_subparsers.add_parser(
        "un",
        help="List unparsed and uncategorized files in OFS structure"
    )
    un_parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to analyze (default: current directory)"
    )
    un_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    un_parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: print to stdout)"
    )
    un_parser.add_argument(
        "--recursive",
        action="store_true",
        default=True,
        help="Process subdirectories recursively (default: True)"
    )
    un_parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Disable recursive processing"
    )

    return parser


def handle_get_path(name: str) -> None:
    """
    Handle the get-path command.

    Args:
        name (str): Name to resolve to a path
    """
    result = get_paths_json(name)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def handle_list() -> None:
    """
    Handle the list command.
    """
    items = list_ofs_items()
    for item in items:
        print(item)


def handle_list_projects() -> None:
    """
    Handle the list-projects command.
    """
    result = list_projects_json()
    print(json.dumps(result, indent=2, ensure_ascii=False))


def handle_list_bidders(project: str) -> None:
    """
    Handle the list-bidders command.

    Args:
        project (str): Project name to list bidders for
    """
    bidders = list_bidders(project)
    result = {
        "project": project,
        "bidders": bidders,
        "total_bidders": len(bidders)
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


def handle_find_bidder(project: str, bidder: str) -> None:
    """
    Handle the find-bidder command.

    Args:
        project (str): Project name
        bidder (str): Bidder name
    """
    path = find_bidder_in_project(project, bidder)
    if path:
        print(path)
    else:
        logger.error(f"Bidder '{bidder}' not found in project '{project}'")
        sys.exit(1)


def handle_list_docs(project_bidder: str, meta: bool = False) -> None:
    """
    Handle the list-docs command.

    Args:
        project_bidder (str): Project name, 'project@bidder', or 'project@bidder@filename' format
        meta (bool): Whether to include detailed metadata for each document (ignored for specific document lookup)
    """
    # Check the format based on number of @ symbols
    if '@' in project_bidder:
        parts = project_bidder.split('@')

        if len(parts) == 2:
            # Determine if this is project@bidder or project@document format
            project, second_part = parts
            project = project.strip()
            second_part = second_part.strip()

            if not project or not second_part:
                print(
                    "Error: Both project and second part must be provided.", file=sys.stderr)
                sys.exit(1)

            # Check if second_part looks like a filename (has an extension)
            # reasonable file extension length
            if '.' in second_part and len(second_part.split('.')[-1]) <= 5:
                # Handle project@document format
                filename = second_part
                result = get_project_document_json(
                    project, filename, include_metadata=meta)
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                # Handle project@bidder format (existing functionality)
                bidder = second_part
                result = list_bidder_docs_json(
                    project, bidder, include_metadata=meta)
                print(json.dumps(result, indent=2, ensure_ascii=False))

            # Exit with error code if there was an error in the result
            if "error" in result:
                sys.exit(1)

        elif len(parts) == 3:
            # Handle project@bidder@filename format (new functionality)
            project, bidder, filename = parts
            project = project.strip()
            bidder = bidder.strip()
            filename = filename.strip()

            if not project or not bidder or not filename:
                print(
                    "Error: Project, bidder, and filename must all be provided.", file=sys.stderr)
                sys.exit(1)

            result = get_bidder_document_json(
                project, bidder, filename, include_metadata=meta)
            print(json.dumps(result, indent=2, ensure_ascii=False))

            # Exit with error code if there was an error in the result
            if "error" in result:
                sys.exit(1)

        else:
            logger.error(
                "Invalid format. Use 'project', 'project@bidder', or 'project@bidder@filename' format.")
            sys.exit(1)
    else:
        # Handle project-only format (existing functionality)
        project = project_bidder.strip()

        if not project:
            logger.error("Project name must be provided.")
            sys.exit(1)

        result = list_project_docs_json(project, include_metadata=meta)
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # Exit with error code if there was an error in the result
        if "error" in result:
            sys.exit(1)


def handle_root() -> None:
    """
    Handle the root command.
    """
    root = get_ofs_root()
    if root:
        print(root)
    else:
        logger.error("OFS root not found")
        sys.exit(1)


def handle_tree(directories_only: bool = False) -> None:
    """
    Handle the tree command.

    Args:
        directories_only (bool): Whether to show only directories (no documents)
    """
    tree_output = print_tree_structure(directories_only)
    print(tree_output)


def handle_read_doc(identifier: str, parser_name: Optional[str] = None, as_json: bool = False) -> None:
    """
    Handle the read-doc command.

    Args:
        identifier (str): Identifier in the form 'Project@Filename' (tender docs) or 'Project@Bidder@Filename' (bidder docs)
        parser_name (Optional[str]): Optional parser to use
        as_json (bool): Whether to output the full JSON result
    """
    result = read_doc(identifier, parser=parser_name)

    if as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if not result.get("success", False):
            sys.exit(1)
        return

    if not result.get("success", False):
        print(
            f"Error: {result.get('error', 'Unknown error')}\nPath: {result.get('file_path', '')}", file=sys.stderr)
        sys.exit(1)

    content = result.get("content", "")
    print(content)


def handle_kriterien(project: str, action: str, limit: Optional[int] = None, tag_id: Optional[str] = None) -> None:
    """
    Handle the kriterien command.

    Args:
        project (str): Project name
        action (str): Action to perform (pop, tree, tag)
        limit (Optional[int]): Number of criteria to show for pop action
        tag_id (Optional[str]): Tag ID for tag action
    """
    if action == "pop":
        result = get_kriterien_pop_json(project, limit or 1)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if "error" in result:
            sys.exit(1)
    elif action == "tree":
        result = get_kriterien_tree_json(project)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if "error" in result:
            sys.exit(1)
    elif action == "tag":
        result = get_kriterien_tag_json(project, tag_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if "error" in result:
            sys.exit(1)
    else:
        logger.error(f"Unknown kriterien action: {action}")
        sys.exit(1)


def handle_index(action: str, directory: str, recursive: bool = False, force: bool = False, max_age: int = 24,
                 json_output: bool = False, output_file: str = None) -> None:
    """
    Handle index management commands.

    Args:
        action: Index action to perform (create, update, clear, stats, un)
        directory: Directory to operate on
        recursive: Whether to operate recursively
        force: Whether to force overwrite (for create)
        max_age: Maximum age in hours for update
        json_output: Whether to output in JSON format (for un action)
        output_file: Output file path (for un action)
    """
    import os

    # If directory is current directory (.), use OFS root instead
    if directory == '.':
        ofs_root = get_ofs_root()
        if ofs_root:
            directory = ofs_root
        else:
            logger.error("OFS root not found. Please run from an OFS project directory.")
            sys.exit(1)

    # Convert relative path to absolute path
    try:
        directory = os.path.abspath(directory)

        if not os.path.exists(directory):
            logger.error(f"Directory '{directory}' does not exist.")
            sys.exit(1)

        if not os.path.isdir(directory):
            logger.error(f"'{directory}' is not a directory.")
            sys.exit(1)
    except (OSError, PermissionError) as e:
        logger.error(f"Error accessing directory '{directory}': {e}")
        sys.exit(1)

    try:
        if action == "create":
            success = create_index(directory, recursive=recursive, force=force)
            if not success:
                sys.exit(1)
        elif action == "update":
            success = update_index(
                directory, recursive=recursive, max_age_hours=max_age)
            if not success:
                sys.exit(1)
        elif action == "clear":
            success = clear_index(directory, recursive=recursive)
            if not success:
                sys.exit(1)
        elif action == "stats":
            print_index_stats(directory)
        elif action == "un":
            from .index import generate_un_items_list
            generate_un_items_list(
                directory, output_file, json_output, recursive)
        else:
            logger.error(f"Unknown index action: {action}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error during index {action}: {e}")
        sys.exit(1)


def main(argv: Optional[list[str]] = None) -> int:
    """
    Main entry point for the OFS CLI.

    Args:
        argv (Optional[list[str]]): Command line arguments (defaults to sys.argv)

    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    try:
        if args.command == "get-path":
            handle_get_path(args.name)
        elif args.command == "list":
            handle_list()
        elif args.command == "list-projects":
            handle_list_projects()
        elif args.command == "list-bidders":
            handle_list_bidders(args.project)
        elif args.command == "find-bidder":
            handle_find_bidder(args.project, args.bidder)
        elif args.command == "list-docs":
            handle_list_docs(args.project_bidder, args.meta)
        elif args.command == "root":
            handle_root()
        elif args.command == "tree":
            handle_tree(args.directories)
        elif args.command == "read-doc":
            handle_read_doc(args.identifier, args.parser, args.json)
        elif args.command == "kriterien":
            if not args.kriterien_action:
                logger.error(
                    "kriterien command requires an action (pop, tree, tag)")
                return 1
            limit = getattr(args, 'limit', None)
            tag_id = getattr(args, 'tag_id', None)
            handle_kriterien(
                args.project, args.kriterien_action, limit, tag_id)
        elif args.command == "index":
            if not args.index_action:
                logger.error(
                    "index command requires an action (create, update, clear, stats)")
                return 1
            directory = getattr(args, 'directory', '.')
            recursive = getattr(args, 'recursive', False)
            force = getattr(args, 'force', False)
            max_age = getattr(args, 'max_age', 24)

            # Handle 'un' action specific parameters
            json_output = getattr(args, 'json', False)
            output_file = getattr(args, 'output', None)

            # Handle --no-recursive flag for 'un' action
            if args.index_action == 'un' and getattr(args, 'no_recursive', False):
                recursive = False

            handle_index(args.index_action, directory, recursive,
                         force, max_age, json_output, output_file)
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1

        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
