"""Command Line Interface for OFS (Opinionated Filesystem).

Provides command-line access to OFS functionality.
"""

import sys
import json
import argparse
from typing import Optional

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
    list_project_docs_json
)


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
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
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
        help="Project name or 'project@bidder' format"
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
    result = list_bidders_json(project)
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
        print(f"Bidder '{bidder}' not found in project '{project}'")
        sys.exit(1)


def handle_list_docs(project_bidder: str, meta: bool = False) -> None:
    """
    Handle the list-docs command.
    
    Args:
        project_bidder (str): Project name or 'project@bidder' format
        meta (bool): Whether to include detailed metadata for each document
    """
    # Check if it's project@bidder format or just project name
    if '@' in project_bidder:
        # Handle project@bidder format (existing functionality)
        try:
            project, bidder = project_bidder.split('@', 1)
            project = project.strip()
            bidder = bidder.strip()
            
            if not project or not bidder:
                print("Error: Both project and bidder names must be provided.", file=sys.stderr)
                sys.exit(1)
            
            result = list_bidder_docs_json(project, bidder, include_metadata=meta)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Exit with error code if there was an error in the result
            if "error" in result:
                sys.exit(1)
                
        except ValueError:
            print("Error: Invalid format. Use 'project@bidder' format.", file=sys.stderr)
            sys.exit(1)
    else:
        # Handle project-only format (new functionality)
        project = project_bidder.strip()
        
        if not project:
            print("Error: Project name must be provided.", file=sys.stderr)
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
        print("OFS root not found", file=sys.stderr)
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
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1
            
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())