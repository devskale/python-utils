"""
JSON File Management Module for OFS

This module provides functionality to read and update JSON files in the OFS structure,
specifically projekt.json and audit.json files.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Union
from datetime import datetime

from .config import get_config
from .paths import get_path


def read_json_file(project: str, filename: str, key_path: Optional[str] = None) -> Union[Dict[str, Any], Any]:
    """
    Read a JSON file from the OFS structure.

    Args:
        project: The project name (AUSSCHREIBUNGNAME)
        filename: The JSON filename ('projekt.json' or 'audit.json')
        key_path: Optional dot-separated path to a specific key (e.g., 'meta.version')

    Returns:
        The JSON content or specific value if key_path is provided

    Raises:
        FileNotFoundError: If the JSON file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        KeyError: If the specified key_path doesn't exist
        ValueError: If filename is not supported
    """
    # Validate filename
    supported_files = ['projekt.json', 'audit.json']
    if filename not in supported_files:
        raise ValueError(
            f"Unsupported filename '{filename}'. Supported files: {supported_files}")

    # Get project path
    try:
        project_path = get_path(project)
        if not project_path:
            raise FileNotFoundError(f"Project '{project}' not found")
    except Exception as e:
        raise FileNotFoundError(f"Error finding project '{project}': {str(e)}")

    # Construct file path
    if filename == 'projekt.json':
        json_file_path = os.path.join(project_path, filename)
    elif filename == 'audit.json':
        # audit.json is typically in bidder directories, but we'll check project root first
        json_file_path = os.path.join(project_path, filename)
        if not os.path.exists(json_file_path):
            # Look for audit.json in bidder directories
            bidder_dirs = []
            b_path = os.path.join(project_path, 'B')
            if os.path.exists(b_path):
                for item in os.listdir(b_path):
                    bidder_path = os.path.join(b_path, item)
                    if os.path.isdir(bidder_path):
                        audit_path = os.path.join(bidder_path, 'audit.json')
                        if os.path.exists(audit_path):
                            bidder_dirs.append(audit_path)

            if bidder_dirs:
                # Return the first found audit.json or ask for specific bidder
                json_file_path = bidder_dirs[0]
            else:
                raise FileNotFoundError(
                    f"No audit.json found in project '{project}'")

    # Check if file exists
    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"JSON file not found: {json_file_path}")

    # Read and parse JSON
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in {json_file_path}: {str(e)}", e.doc, e.pos)

    # Return specific key if requested
    if key_path:
        return _get_nested_value(data, key_path)

    return data


def read_audit_json(project: str, bidder: str, key_path: Optional[str] = None) -> Union[Dict[str, Any], Any]:
    """
    Read audit.json from a specific bidder directory.

    Args:
        project: The project name (AUSSCHREIBUNGNAME)
        bidder: The bidder name (BIETERNAME)
        key_path: Optional dot-separated path to a specific key

    Returns:
        The JSON content or specific value if key_path is provided

    Raises:
        FileNotFoundError: If the audit.json file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        KeyError: If the specified key_path doesn't exist
    """
    # Get project path
    try:
        project_path = get_path(project)
        if not project_path:
            raise FileNotFoundError(f"Project '{project}' not found")
    except Exception as e:
        raise FileNotFoundError(f"Error finding project '{project}': {str(e)}")

    # Construct bidder audit.json path
    audit_file_path = os.path.join(project_path, 'B', bidder, 'audit.json')

    # Check if file exists
    if not os.path.exists(audit_file_path):
        raise FileNotFoundError(
            f"audit.json not found for bidder '{bidder}' in project '{project}': {audit_file_path}")

    # Read and parse JSON
    try:
        with open(audit_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in {audit_file_path}: {str(e)}", e.doc, e.pos)

    # Return specific key if requested
    if key_path:
        return _get_nested_value(data, key_path)

    return data


def update_json_file(project: str, filename: str, key_path: str, value: Any,
                     create_backup: bool = True) -> bool:
    """
    Update a specific key in a JSON file with atomic write operations.

    Args:
        project: The project name (AUSSCHREIBUNGNAME)
        filename: The JSON filename ('projekt.json' or 'audit.json')
        key_path: Dot-separated path to the key to update (e.g., 'meta.version')
        value: The new value to set
        create_backup: Whether to create a backup before updating

    Returns:
        True if update was successful

    Raises:
        FileNotFoundError: If the JSON file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        ValueError: If filename is not supported or key_path is invalid
    """
    # Validate filename
    supported_files = ['projekt.json', 'audit.json']
    if filename not in supported_files:
        raise ValueError(
            f"Unsupported filename '{filename}'. Supported files: {supported_files}")

    # Get project path
    try:
        project_path = get_path(project)
        if not project_path:
            raise FileNotFoundError(f"Project '{project}' not found")
    except Exception as e:
        raise FileNotFoundError(f"Error finding project '{project}': {str(e)}")

    # Construct file path
    json_file_path = os.path.join(project_path, filename)

    # Check if file exists
    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"JSON file not found: {json_file_path}")

    # Create backup if requested
    if create_backup:
        backup_path = f"{json_file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(json_file_path, backup_path)

    # Read current data
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in {json_file_path}: {str(e)}", e.doc, e.pos)

    # Update the nested value
    _set_nested_value(data, key_path, value)

    # Write atomically (write to temp file, then rename)
    temp_file_path = f"{json_file_path}.tmp"
    try:
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Atomic rename
        os.rename(temp_file_path, json_file_path)
        return True

    except Exception as e:
        # Clean up temp file if it exists
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise e


def update_audit_json(project: str, bidder: str, key_path: str, value: Any,
                      create_backup: bool = True) -> bool:
    """
    Update a specific key in audit.json for a specific bidder.

    Args:
        project: The project name (AUSSCHREIBUNGNAME)
        bidder: The bidder name (BIETERNAME)
        key_path: Dot-separated path to the key to update
        value: The new value to set
        create_backup: Whether to create a backup before updating

    Returns:
        True if update was successful

    Raises:
        FileNotFoundError: If the audit.json file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        ValueError: If key_path is invalid
    """
    # Get project path
    try:
        project_path = get_path(project)
        if not project_path:
            raise FileNotFoundError(f"Project '{project}' not found")
    except Exception as e:
        raise FileNotFoundError(f"Error finding project '{project}': {str(e)}")

    # Construct bidder audit.json path
    audit_file_path = os.path.join(project_path, 'B', bidder, 'audit.json')

    # Check if file exists
    if not os.path.exists(audit_file_path):
        raise FileNotFoundError(
            f"audit.json not found for bidder '{bidder}' in project '{project}': {audit_file_path}")

    # Create backup if requested
    if create_backup:
        backup_path = f"{audit_file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(audit_file_path, backup_path)

    # Read current data
    try:
        with open(audit_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in {audit_file_path}: {str(e)}", e.doc, e.pos)

    # Update the nested value
    _set_nested_value(data, key_path, value)

    # Write atomically (write to temp file, then rename)
    temp_file_path = f"{audit_file_path}.tmp"
    try:
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Atomic rename
        os.rename(temp_file_path, audit_file_path)
        return True

    except Exception as e:
        # Clean up temp file if it exists
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise e


def _get_nested_value(data: Dict[str, Any], key_path: str) -> Any:
    """
    Get a nested value from a dictionary using dot notation.

    Args:
        data: The dictionary to search
        key_path: Dot-separated path (e.g., 'meta.version')

    Returns:
        The value at the specified path

    Raises:
        KeyError: If the path doesn't exist
    """
    keys = key_path.split('.')
    current = data

    for key in keys:
        # Handle array indices
        if key.isdigit() and isinstance(current, list):
            index = int(key)
            if index >= len(current):
                raise KeyError(
                    f"Array index {index} out of range in path '{key_path}'")
            current = current[index]
        elif isinstance(current, dict):
            if key not in current:
                raise KeyError(f"Key '{key}' not found in path '{key_path}'")
            current = current[key]
        else:
            raise KeyError(
                f"Cannot access key '{key}' in non-dict/non-list object in path '{key_path}'")

    return current


def _set_nested_value(data: Dict[str, Any], key_path: str, value: Any) -> None:
    """
    Set a nested value in a dictionary using dot notation.

    Args:
        data: The dictionary to modify
        key_path: Dot-separated path (e.g., 'meta.version')
        value: The value to set

    Raises:
        ValueError: If the path is invalid or cannot be set
    """
    keys = key_path.split('.')
    current = data

    # Navigate to the parent of the target key
    for key in keys[:-1]:
        # Handle array indices
        if key.isdigit() and isinstance(current, list):
            index = int(key)
            if index >= len(current):
                raise ValueError(
                    f"Array index {index} out of range in path '{key_path}'")
            current = current[index]
        elif isinstance(current, dict):
            if key not in current:
                # Create missing intermediate objects
                current[key] = {}
            current = current[key]
        else:
            raise ValueError(
                f"Cannot access key '{key}' in non-dict/non-list object in path '{key_path}'")

    # Set the final value
    final_key = keys[-1]
    if final_key.isdigit() and isinstance(current, list):
        index = int(final_key)
        if index >= len(current):
            raise ValueError(
                f"Array index {index} out of range in path '{key_path}'")
        current[index] = value
    elif isinstance(current, dict):
        current[final_key] = value
    else:
        raise ValueError(
            f"Cannot set key '{final_key}' in non-dict/non-list object in path '{key_path}'")
