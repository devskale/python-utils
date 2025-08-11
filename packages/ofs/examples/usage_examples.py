#!/usr/bin/env python3
"""
OFS Package Usage Examples

This file demonstrates how to import and use the OFS package functions
in your own Python code.
"""

import json
from pathlib import Path

# Import OFS functions - you can import individual functions or the whole package
from ofs import (
    list_projects,           # Returns simple list of project names
    list_projects_json,      # Returns structured JSON with projects and count
    list_bidders,           # Returns simple list of bidders for a project
    list_bidders_json,      # Returns structured JSON with bidders and files
    get_paths_json,         # Returns structured JSON with all paths for a name
    get_base_dir,           # Get the OFS base directory
    find_bidder_in_project  # Find specific bidder in project
)

# Alternative import style - import the whole package
# import ofs


def example_list_projects_simple():
    """
    Example: Get a simple list of project names
    """
    print("=== Simple Project List ===")
    
    # Get list of all projects (returns list[str])
    projects = list_projects()
    
    print(f"Found {len(projects)} projects:")
    for project in projects:
        print(f"  - {project}")
    
    return projects


def example_list_projects_json():
    """
    Example: Get structured project data in JSON format
    """
    print("\n=== Structured Project Data ===")
    
    # Get structured project data (returns Dict[str, Any])
    project_data = list_projects_json()
    
    print("Project data structure:")
    print(json.dumps(project_data, indent=2, ensure_ascii=False))
    
    # Access individual fields
    print(f"\nTotal projects: {project_data['count']}")
    print("Project names:")
    for project in project_data['projects']:
        print(f"  - {project}")
    
    return project_data


def example_list_bidders_for_project(project_name: str):
    """
    Example: Get bidders for a specific project
    
    Args:
        project_name (str): Name of the project to get bidders for
    """
    print(f"\n=== Bidders for Project: {project_name} ===")
    
    # Simple bidder list (returns list[str])
    bidders = list_bidders(project_name)
    print(f"Simple bidder list ({len(bidders)} items):")
    for bidder in bidders:
        print(f"  - {bidder}")
    
    # Structured bidder data (returns Dict[str, Any])
    bidder_data = list_bidders_json(project_name)
    print(f"\nStructured bidder data:")
    print(json.dumps(bidder_data, indent=2, ensure_ascii=False))
    
    # Access individual fields
    if 'error' not in bidder_data:
        print(f"\nBidder directories: {bidder_data['total_bidders']}")
        print(f"Total files: {bidder_data['total_files']}")
        
        print("\nActual bidders (directories):")
        for bidder in bidder_data['bidder_directories']:
            print(f"  - {bidder}")
    
    return bidder_data


def example_search_paths(search_name: str):
    """
    Example: Search for all paths containing a specific name
    
    Args:
        search_name (str): Name to search for
    """
    print(f"\n=== Searching for: {search_name} ===")
    
    # Get all paths for a name (returns Dict[str, Any])
    path_data = get_paths_json(search_name)
    
    print("Search results:")
    print(json.dumps(path_data, indent=2, ensure_ascii=False))
    
    # Process results
    if path_data['count'] > 0:
        print(f"\nFound {path_data['count']} occurrences:")
        for path_info in path_data['paths']:
            print(f"  - {path_info['path']} (type: {path_info['type']})")
    else:
        print(f"No occurrences found for '{search_name}'")
    
    return path_data


def example_find_specific_bidder(project_name: str, bidder_name: str):
    """
    Example: Find a specific bidder in a project
    
    Args:
        project_name (str): Name of the project
        bidder_name (str): Name of the bidder to find
    """
    print(f"\n=== Finding Bidder: {bidder_name} in Project: {project_name} ===")
    
    try:
        # Find specific bidder (returns str path or raises exception)
        bidder_path = find_bidder_in_project(project_name, bidder_name)
        print(f"Found bidder at: {bidder_path}")
        return bidder_path
    except Exception as e:
        print(f"Bidder not found: {e}")
        return None


def example_get_ofs_info():
    """
    Example: Get OFS configuration information
    """
    print("\n=== OFS Configuration ===")
    
    # Get base directory
    base_dir = get_base_dir()
    print(f"OFS Base Directory: {base_dir}")
    
    # Check if directory exists
    base_path = Path(base_dir)
    if base_path.exists():
        print(f"Directory exists: Yes")
        print(f"Is directory: {base_path.is_dir()}")
    else:
        print(f"Directory exists: No")
    
    return base_dir


def main():
    """
    Main function demonstrating all examples
    """
    print("OFS Package Usage Examples")
    print("=" * 50)
    
    # Get OFS info
    example_get_ofs_info()
    
    # List projects
    projects = example_list_projects_simple()
    project_data = example_list_projects_json()
    
    # If we have projects, demonstrate bidder functionality
    if projects:
        # Use the first project for examples
        first_project = projects[0]
        
        # List bidders for the first project
        example_list_bidders_for_project(first_project)
        
        # Search for specific items
        example_search_paths("pdf")
        example_search_paths(first_project)
        
        # Try to find a specific bidder (this might fail if bidder doesn't exist)
        example_find_specific_bidder(first_project, "Bieter1")
    else:
        print("\nNo projects found in OFS structure.")


if __name__ == "__main__":
    main()