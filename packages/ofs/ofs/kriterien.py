#!/usr/bin/env python3
"""
Kriterien JSON Parser for OFS (Opinionated Filesystem)

A module to parse and analyze criteria from JSON files within the OFS structure.
Integrated from the standalone kriterien.py tool.
"""

import json
import os
from typing import Dict, List, Any, Optional
from collections import defaultdict

from .paths import get_path, get_ofs_root


def load_kriterien(file_path: str) -> Dict[str, Any]:
    """
    Load criteria from JSON file.
    
    Args:
        file_path (str): Path to the JSON criteria file
        
    Returns:
        Dict[str, Any]: Loaded criteria data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the JSON is invalid
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Criteria file '{file_path}' not found.")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in file '{file_path}': {e}", e.doc, e.pos)


def find_kriterien_file(project_name: str) -> Optional[str]:
    """
    Find the kriterien JSON file for a given project in the OFS structure.
    
    Args:
        project_name (str): Name of the project (AUSSCHREIBUNGNAME)
        
    Returns:
        Optional[str]: Path to the kriterien file if found, None otherwise
    """
    try:
        # Get the OFS root and construct the full project path
        ofs_root = get_ofs_root()
        project_relative_path = get_path(project_name)
        
        if not project_relative_path:
            return None
        
        # Try both the returned path and the .dir path
        possible_project_paths = [
            os.path.join(ofs_root, project_relative_path),
            os.path.join(ofs_root, '.dir', project_name)
        ]
        
        for project_path in possible_project_paths:
            if not os.path.exists(project_path):
                continue
                
            # Look for kriterien files in common locations
            possible_files = [
                os.path.join(project_path, 'kriterien.json'),
                os.path.join(project_path, 'kriterien', 'kriterien.json'),
                os.path.join(project_path, 'A', 'kriterien.json'),
                os.path.join(project_path, 'kriterien.all.json'),
                os.path.join(project_path, 'kriterien', 'kriterien.all.json'),
            ]
            
            # Also search for any .json files containing 'kriterien' in the name
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    if 'kriterien' in file.lower() and file.endswith('.json'):
                        possible_files.append(os.path.join(root, file))
            
            # Return the first existing file
            for file_path in possible_files:
                if os.path.exists(file_path):
                    return file_path
                
        return None
        
    except Exception:
        return None


def get_unproven_kriterien(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get all criteria that haven't been proven yet (status is null).
    
    Args:
        data (Dict[str, Any]): Loaded criteria data
        
    Returns:
        List[Dict[str, Any]]: List of unproven criteria
    """
    unproven = []
    
    # Handle both old format (kriterien array) and new format (extractedCriteria structure)
    if 'kriterien' in data:
        # New flat format with kriterien array
        for kriterium in data.get('kriterien', []):
            pruefung = kriterium.get('pruefung', {})
            if pruefung.get('status') is None:
                unproven.append(kriterium)
    elif 'extractedCriteria' in data:
        # Old nested format - flatten the nested structure
        extracted = data['extractedCriteria']
        for category_name, category_data in extracted.items():
            if isinstance(category_data, dict):
                for subcategory_name, subcategory_data in category_data.items():
                    if isinstance(subcategory_data, list):
                        for item in subcategory_data:
                            if isinstance(item, dict):
                                # Add category and subcategory info to the item
                                enhanced_item = item.copy()
                                enhanced_item['category'] = category_name
                                enhanced_item['subcategory'] = subcategory_name
                                # Check if it's unproven (no pruefung status)
                                pruefung = enhanced_item.get('pruefung', {})
                                if pruefung.get('status') is None:
                                    unproven.append(enhanced_item)
    
    return unproven


def build_kriterien_tree(data: Dict[str, Any]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    """
    Build a tree structure of criteria organized by categories and subcategories.
    
    Args:
        data (Dict[str, Any]): Loaded criteria data
        
    Returns:
        Dict[str, Dict[str, List[Dict[str, Any]]]]: Tree structure of criteria
    """
    tree = defaultdict(lambda: defaultdict(list))
    
    # Handle both old format (kriterien array) and new format (extractedCriteria structure)
    if 'kriterien' in data:
        # New flat format with kriterien array
        for kriterium in data.get('kriterien', []):
            category = kriterium.get('kategorie', kriterium.get('category', 'Unknown'))
            subcategory = kriterium.get('typ', kriterium.get('subcategory', 'General'))
            tree[category][subcategory].append(kriterium)
    elif 'extractedCriteria' in data:
        # Old nested format - use the existing structure
        extracted = data['extractedCriteria']
        for category_name, category_data in extracted.items():
            if isinstance(category_data, dict):
                for subcategory_name, subcategory_data in category_data.items():
                    if isinstance(subcategory_data, list):
                        for item in subcategory_data:
                            if isinstance(item, dict):
                                # Add category and subcategory info to the item
                                enhanced_item = item.copy()
                                enhanced_item['category'] = category_name
                                enhanced_item['subcategory'] = subcategory_name
                                tree[category_name][subcategory_name].append(enhanced_item)
            elif isinstance(category_data, list):
                # Handle direct lists under categories
                for item in category_data:
                    if isinstance(item, dict):
                        enhanced_item = item.copy()
                        enhanced_item['category'] = category_name
                        enhanced_item['subcategory'] = 'General'
                        tree[category_name]['General'].append(enhanced_item)
    
    return dict(tree)


def get_kriterien_by_tag(data: Dict[str, Any], tag_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific criterion by its tag/ID.
    
    Args:
        data (Dict[str, Any]): Loaded criteria data
        tag_id (str): The tag/ID to search for
        
    Returns:
        Optional[Dict[str, Any]]: The criterion if found, None otherwise
    """
    # Handle both old format (kriterien array) and new format (extractedCriteria structure)
    if 'kriterien' in data:
        # New flat format with kriterien array
        for kriterium in data.get('kriterien', []):
            if kriterium.get('id') == tag_id or kriterium.get('tag') == tag_id:
                return kriterium
    elif 'extractedCriteria' in data:
        # Old nested format - search through all criteria
        extracted = data['extractedCriteria']
        for category_name, category_data in extracted.items():
            if isinstance(category_data, dict):
                for subcategory_name, subcategory_data in category_data.items():
                    if isinstance(subcategory_data, list):
                        for item in subcategory_data:
                            if isinstance(item, dict):
                                if item.get('id') == tag_id or item.get('tag') == tag_id:
                                    enhanced_item = item.copy()
                                    enhanced_item['category'] = category_name
                                    enhanced_item['subcategory'] = subcategory_name
                                    return enhanced_item
    return None


def get_all_kriterien_tags(data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Get all available criterion tags/IDs with their names.
    
    Args:
        data (Dict[str, Any]): Loaded criteria data
        
    Returns:
        List[Dict[str, str]]: List of tag dictionaries with 'id' and 'name' keys
    """
    tags = []
    
    # Handle both old format (kriterien array) and new format (extractedCriteria structure)
    if 'kriterien' in data:
        # New flat format with kriterien array
        for kriterium in data.get('kriterien', []):
            tag_id = kriterium.get('id')
            name = kriterium.get('name', kriterium.get('kriterium', 'Unknown'))
            if tag_id:
                tags.append({
                    'id': tag_id,
                    'name': name
                })
    elif 'extractedCriteria' in data:
        # Old nested format - search through all criteria
        extracted = data['extractedCriteria']
        for category_name, category_data in extracted.items():
            if isinstance(category_data, dict):
                for subcategory_name, subcategory_data in category_data.items():
                    if isinstance(subcategory_data, list):
                        for item in subcategory_data:
                            if isinstance(item, dict):
                                tag_id = item.get('id')
                                name = item.get('name', item.get('kriterium', 'Unknown'))
                                if tag_id:
                                    tags.append({
                                        'id': tag_id,
                                        'name': name
                                    })
    
    return tags


def format_kriterien_list(kriterien: List[Dict[str, Any]], limit: Optional[int] = None, 
                         total_kriterien: int = 0, proven_count: int = 0) -> str:
    """
    Format a list of criteria for display.
    
    Args:
        kriterien (List[Dict[str, Any]]): List of criteria to format
        limit (Optional[int]): Maximum number of criteria to show
        total_kriterien (int): Total number of criteria
        proven_count (int): Number of proven criteria
        
    Returns:
        str: Formatted string representation
    """
    if limit is not None:
        kriterien = kriterien[:limit]
    
    if not kriterien:
        return "No unproven criteria found."
    
    # Calculate checked and remaining numbers
    checked_num = proven_count
    total_num = total_kriterien
    
    output = []
    output.append(f"\n{total_num - checked_num} von {total_num} Kriterien verbleiben zur Prüfung.")
    output.append("=" * 80)
    
    for i, kriterium in enumerate(kriterien, 1):
        output.append(f"{i:2d}. Complete Kriterium Data:")
        output.append("-" * 80)
        output.append(json.dumps(kriterium, indent=2, ensure_ascii=False))
        output.append("-" * 80)
    
    return "\n".join(output)


def format_kriterien_tree(data: Dict[str, Any]) -> str:
    """
    Format criteria in a tree structure organized by typ and kategorie.
    
    Args:
        data (Dict[str, Any]): Loaded criteria data
        
    Returns:
        str: Formatted tree structure
    """
    tree = build_kriterien_tree(data)
    
    output = []
    output.append("\nKriterien Tree (sorted by Typ and Kategorie):")
    output.append("=" * 80)
    
    for typ in sorted(tree.keys()):
        output.append(f"\n📁 Typ: {typ}")
        output.append("-" * 40)
        
        for kategorie in sorted(tree[typ].keys()):
            kriterien_list = tree[typ][kategorie]
            unproven_count = sum(1 for k in kriterien_list if k.get('pruefung', {}).get('status') is None)
            proven_count = len(kriterien_list) - unproven_count
            
            output.append(f"  📂 Kategorie: {kategorie}")
            output.append(f"     Total: {len(kriterien_list)}, Unproven: {unproven_count}, Proven: {proven_count}")
            
            # Show unproven criteria in this category
            unproven_in_cat = [k for k in kriterien_list if k.get('pruefung', {}).get('status') is None]
            if unproven_in_cat:
                output.append(f"     Unproven criteria:")
                for kriterium in unproven_in_cat:
                    output.append(f"       • {kriterium['id']}: {kriterium['name']}")
            output.append("")
    
    return "\n".join(output)


def format_kriterien_tags(data: Dict[str, Any]) -> str:
    """
    Format all available criterion tags for display.
    
    Args:
        data (Dict[str, Any]): Loaded criteria data
        
    Returns:
        str: Formatted list of all tags
    """
    tags = get_all_kriterien_tags(data)
    if not tags:
        return "No criteria found in the data."
    
    output = []
    output.append(f"\nAll available criterion tags ({len(tags)} total):")
    output.append("=" * 80)
    for tag in tags:
        output.append(f"  • {tag['id']}: {tag['name']}")
    output.append("=" * 80)
    
    return "\n".join(output)


def format_kriterium_by_tag(data: Dict[str, Any], tag_id: str) -> str:
    """
    Format a specific criterion by its ID tag for display.
    
    Args:
        data (Dict[str, Any]): Loaded criteria data
        tag_id (str): The criterion ID to display
        
    Returns:
        str: Formatted criterion data or error message
    """
    # If no tag_id provided (empty string), list all tags
    if not tag_id:
        return format_kriterien_tags(data)
    
    kriterium = get_kriterien_by_tag(data, tag_id)
    if kriterium:
        output = []
        output.append(f"\nKriterium found: {tag_id}")
        output.append("=" * 80)
        output.append(json.dumps(kriterium, indent=2, ensure_ascii=False))
        output.append("=" * 80)
        return "\n".join(output)
    else:
        output = []
        output.append(f"\nError: Kriterium with ID '{tag_id}' not found.")
        output.append("Available IDs:")
        tags = get_all_kriterien_tags(data)
        for tag in tags:
            output.append(f"  • {tag['id']}: {tag['name']}")
        return "\n".join(output)


# JSON API functions for CLI integration

def get_kriterien_pop_json(project_name: str, limit: int = 1) -> Dict[str, Any]:
    """
    Get unproven criteria in JSON format for CLI output.
    
    Args:
        project_name (str): Name of the project
        limit (int): Number of criteria to return
        
    Returns:
        Dict[str, Any]: JSON response with criteria data or error
    """
    try:
        kriterien_file = find_kriterien_file(project_name)
        if not kriterien_file:
            return {
                "error": f"No kriterien file found for project '{project_name}'",
                "project": project_name
            }
        
        data = load_kriterien(kriterien_file)
        unproven_kriterien = get_unproven_kriterien(data)
        total_kriterien = len(data.get('kriterien', []))
        proven_count = total_kriterien - len(unproven_kriterien)
        
        if limit is not None:
            displayed_kriterien = unproven_kriterien[:limit]
        else:
            displayed_kriterien = unproven_kriterien
        
        return {
            "project": project_name,
            "kriterien_file": kriterien_file,
            "total_kriterien": total_kriterien,
            "proven_count": proven_count,
            "unproven_count": len(unproven_kriterien),
            "displayed_count": len(displayed_kriterien),
            "limit": limit,
            "kriterien": displayed_kriterien
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "project": project_name
        }


def get_kriterien_tree_json(project_name: str) -> Dict[str, Any]:
    """
    Get criteria tree structure in JSON format for CLI output.
    
    Args:
        project_name (str): Name of the project
        
    Returns:
        Dict[str, Any]: JSON response with tree data or error
    """
    try:
        kriterien_file = find_kriterien_file(project_name)
        if not kriterien_file:
            return {
                "error": f"No kriterien file found for project '{project_name}'",
                "project": project_name
            }
        
        data = load_kriterien(kriterien_file)
        tree = build_kriterien_tree(data)
        unproven_kriterien = get_unproven_kriterien(data)
        total_kriterien = len(data.get('kriterien', []))
        proven_count = total_kriterien - len(unproven_kriterien)
        
        # Build tree summary with counts
        tree_summary = {}
        for typ in tree:
            tree_summary[typ] = {}
            for kategorie in tree[typ]:
                kriterien_list = tree[typ][kategorie]
                unproven_count = sum(1 for k in kriterien_list if k.get('pruefung', {}).get('status') is None)
                proven_count_cat = len(kriterien_list) - unproven_count
                
                tree_summary[typ][kategorie] = {
                    "total": len(kriterien_list),
                    "proven": proven_count_cat,
                    "unproven": unproven_count,
                    "unproven_kriterien": [
                        {
                            "id": k.get('id'),
                            "name": k.get('name')
                        } for k in kriterien_list if k.get('pruefung', {}).get('status') is None
                    ]
                }
        
        return {
            "project": project_name,
            "kriterien_file": kriterien_file,
            "total_kriterien": total_kriterien,
            "proven_count": proven_count,
            "unproven_count": len(unproven_kriterien),
            "tree": tree_summary
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "project": project_name
        }


def get_kriterien_tag_json(project_name: str, tag_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get criterion by tag or all tags in JSON format for CLI output.
    
    Args:
        project_name (str): Name of the project
        tag_id (Optional[str]): Specific tag ID to retrieve, or None for all tags
        
    Returns:
        Dict[str, Any]: JSON response with tag data or error
    """
    try:
        kriterien_file = find_kriterien_file(project_name)
        if not kriterien_file:
            return {
                "error": f"No kriterien file found for project '{project_name}'",
                "project": project_name
            }
        
        data = load_kriterien(kriterien_file)
        
        if tag_id:
            # Get specific criterion
            kriterium = get_kriterien_by_tag(data, tag_id)
            if kriterium:
                return {
                    "project": project_name,
                    "kriterien_file": kriterien_file,
                    "tag_id": tag_id,
                    "kriterium": kriterium
                }
            else:
                return {
                    "error": f"Kriterium with ID '{tag_id}' not found",
                    "project": project_name,
                    "tag_id": tag_id,
                    "available_tags": get_all_kriterien_tags(data)
                }
        else:
            # Get all tags
            tags = get_all_kriterien_tags(data)
            return {
                "project": project_name,
                "kriterien_file": kriterien_file,
                "total_tags": len(tags),
                "tags": tags
            }
        
    except Exception as e:
        return {
            "error": str(e),
            "project": project_name
        }