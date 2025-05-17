# index.py - Index management for PDF to Markdown conversion

import os
import time
import json
import hashlib
from .config import ConfigManager


def create_index(directory: str, recursive: bool = False) -> None:
    """Create fresh .pdf2md_index.json files in each directory.

    Args:
        directory: Root directory to create indexes in
        recursive: Whether to process subdirectories recursively
    """
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories, ./md subdirs, and directories starting with '_'
        dirs[:] = [d for d in dirs if not d.startswith(
            '.') and not d.startswith('_') and d != 'md']

        index_data = {
            'files': [],
            'directories': [],
            'timestamp': time.time()
        }

        # Process files
        for file in files:
            if file.startswith('.') or file.startswith('_'):
                continue

            file_path = os.path.join(root, file)
            lower_file = file.lower()

            if (lower_file.endswith('.pdf') or
                any(lower_file.endswith(ext) for ext in ['.docx', '.xlsx', '.pptx']) or
                    any(lower_file.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif'])):
                # Get file size and hash
                file_size = os.path.getsize(file_path)
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()

                # Check for corresponding .md files
                parsers = []
                md_dir_path = os.path.join(root, 'md')
                if os.path.exists(md_dir_path) and os.path.isdir(md_dir_path):
                    file_base_name = os.path.splitext(file)[0]

                    # 1. Check for Marker parser (md/file_base_name/file_base_name.marker.md)
                    marker_sub_dir = os.path.join(md_dir_path, file_base_name)
                    if os.path.isdir(marker_sub_dir):
                        expected_marker_file_path = os.path.join(
                            marker_sub_dir, file_base_name + ".marker.md")
                        if os.path.exists(expected_marker_file_path) and 'marker' not in parsers:
                            parsers.append('marker')

                    # 2. Check for other parsers (md/file_base_name.parser.md)
                    for item_in_md_dir in os.listdir(md_dir_path):
                        if item_in_md_dir.startswith('.') or item_in_md_dir.startswith('_'):
                            continue

                        item_path_in_md_dir = os.path.join(
                            md_dir_path, item_in_md_dir)

                        # Process only files directly under md_dir_path for non-marker parsers
                        if os.path.isfile(item_path_in_md_dir):
                            # Check if the md file corresponds to the current source file (file_base_name)
                            # and is in the format file_base_name.parser.md
                            if item_in_md_dir.startswith(file_base_name + '.') and item_in_md_dir.endswith('.md'):
                                # Extract parser name: file_base_name.(parser).md
                                potential_parser_name = item_in_md_dir[len(
                                    file_base_name)+1: -len('.md')]

                                # Ensure it's not 'marker' (already handled) and is a valid parser name (not empty)
                                if potential_parser_name and potential_parser_name != 'marker' and potential_parser_name not in parsers:
                                    parsers.append(potential_parser_name)

                index_data['files'].append({
                    'name': file,
                    'size': file_size,
                    'hash': file_hash,
                    'parser': parsers if parsers else ''
                })

        # Process directories
        for dir_name in dirs:
            if not dir_name.startswith('.') and not dir_name.startswith('_') and dir_name != 'md':
                dir_path = os.path.join(root, dir_name)
                dir_size = sum(os.path.getsize(os.path.join(dir_path, f)) for f in os.listdir(
                    dir_path) if os.path.isfile(os.path.join(dir_path, f)))
                dir_hash = hashlib.md5(
                    str(sorted(os.listdir(dir_path))).encode()).hexdigest()

                index_data['directories'].append({
                    'name': dir_name,
                    'size': dir_size,
                    'hash': dir_hash,
                    'parser': ''  # Directories don't have parsers
                })

        # Write index file
        config = ConfigManager()
        index_file_name = config.get('index_file_name')
        index_path = os.path.join(root, index_file_name)
        with open(index_path, 'w') as f:
            json.dump(index_data, f)

        if not recursive:
            break


def update_index(directory: str, max_age: int = 30, recursive: bool = False) -> None:
    """Update existing index files if they're older than max_age seconds.

    Args:
        directory: Root directory to update indexes in
        max_age: Maximum age (in seconds) before index is considered stale
        recursive: Whether to process subdirectories recursively
    """
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories, ./md subdirs, and directories starting with '_'
        dirs[:] = [d for d in dirs if not d.startswith(
            '.') and not d.startswith('_') and d != 'md']

        config = ConfigManager()
        index_file_name = config.get('index_file_name')
        index_path = os.path.join(root, index_file_name)

        if os.path.exists(index_path):
            # Check if index needs updating
            index_age = time.time() - os.path.getmtime(index_path)
            if index_age <= max_age:
                continue

            # Clear existing index to ensure fresh parser list
            os.remove(index_path)

        # Create fresh index with updated parser list
        create_index(root, recursive=False)

        if not recursive:
            break


def clear_index(directory: str, recursive: bool = False) -> None:
    """Remove all .pdf2md_index.json files.

    Args:
        directory: Root directory to clear indexes from
        recursive: Whether to process subdirectories recursively
    """
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories, ./md subdirs, and directories starting with '_'
        dirs[:] = [d for d in dirs if not d.startswith(
            '.') and not d.startswith('_') and d != 'md']

        config = ConfigManager()
        index_file_name = config.get('index_file_name')
        index_path = os.path.join(root, index_file_name)
        if os.path.exists(index_path):
            os.remove(index_path)

        if not recursive:
            break
