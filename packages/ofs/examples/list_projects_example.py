#!/usr/bin/env python3
"""
Simple Example: How to List Projects using OFS Package

This example shows the most common ways to list projects from the OFS structure.
"""

import json

# Method 1: Import specific functions
from ofs import list_projects, list_projects_json

# Method 2: Import the whole package (alternative)
# import ofs


def simple_project_list():
    """
    Get a simple list of project names
    Returns: list[str]
    """
    projects = list_projects()
    print(f"Found {len(projects)} projects:")
    for project in projects:
        print(f"  - {project}")
    return projects


def structured_project_data():
    """
    Get structured project data with metadata
    Returns: Dict[str, Any] with 'projects' and 'count' keys
    """
    data = list_projects_json()
    
    # Pretty print the JSON
    print("Structured project data:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    # Access individual fields
    print(f"\nTotal count: {data['count']}")
    print("Projects list:")
    for project in data['projects']:
        print(f"  - {project}")
    
    return data


def process_projects_programmatically():
    """
    Example of processing projects in your code
    """
    # Get the structured data
    project_data = list_projects_json()
    
    # Process each project
    results = []
    for project_name in project_data['projects']:
        # You can now use project_name for further processing
        project_info = {
            'name': project_name,
            'name_length': len(project_name),
            'has_special_chars': any(c in project_name for c in 'äöüß'),
            # Add more processing as needed
        }
        results.append(project_info)
    
    print("\nProcessed project information:")
    for info in results:
        print(f"  {info['name']}: {info['name_length']} chars, "
              f"special chars: {info['has_special_chars']}")
    
    return results


if __name__ == "__main__":
    print("OFS Project Listing Examples")
    print("=" * 40)
    
    print("\n1. Simple project list:")
    simple_project_list()
    
    print("\n2. Structured project data:")
    structured_project_data()
    
    print("\n3. Programmatic processing:")
    process_projects_programmatically()