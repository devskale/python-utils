# index.py - Index management for PDF to Markdown conversion

import os
import time
import json
import hashlib
from typing import Optional, Dict, List  # Added Optional, Dict, List
from .config import ConfigManager


# Helper function to generate index data for a specific path
def _generate_index_data_for_path(current_root: str, sub_dir_names: List[str], files_in_current_root: List[str]) -> Dict:
    """Generates index data for a specific path, its files, and subdirectories.

    Args:
        current_root: The current directory path being processed.
        sub_dir_names: List of filtered subdirectory names within current_root.
        files_in_current_root: List of all file names within current_root.

    Returns:
        A dictionary containing the index data for the given path.
    """
    index_data = {
        'files': [],
        'directories': [],
        'timestamp': time.time()
    }

    # Process files
    for file_name in files_in_current_root:
        if file_name.startswith('.') or file_name.startswith('_'):
            continue

        file_path = os.path.join(current_root, file_name)
        lower_file = file_name.lower()

        if (lower_file.endswith('.pdf') or
            any(lower_file.endswith(ext) for ext in ['.docx', '.xlsx', '.pptx']) or
                any(lower_file.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif'])):
            # Get file size and hash
            file_size = os.path.getsize(file_path)
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

            # Check for corresponding .md files
            parsers = []
            md_dir_path = os.path.join(current_root, 'md')
            if os.path.exists(md_dir_path) and os.path.isdir(md_dir_path):
                file_base_name = os.path.splitext(file_name)[0]

                # 1. Check for Marker parser (md/file_base_name/file_base_name.marker.md)
                marker_sub_dir = os.path.join(md_dir_path, file_base_name)
                if os.path.isdir(marker_sub_dir):
                    expected_marker_file_path = os.path.join(
                        marker_sub_dir, file_base_name + ".marker.md")
                    if os.path.exists(expected_marker_file_path) and 'marker' not in parsers:
                        parsers.append('marker')

                # 1b. Check for md/<basename>.md (plain md file, treat as parser "md")
                plain_md_file_path = os.path.join(
                    md_dir_path, file_base_name + ".md")
                if os.path.isfile(plain_md_file_path) and 'md' not in parsers:
                    parsers.append('md')

                # 2. Check for other parsers (md/file_base_name.parser.md)
                for item_in_md_dir in os.listdir(md_dir_path):
                    if item_in_md_dir.startswith('.') or item_in_md_dir.startswith('_'):
                        continue

                    item_path_in_md_dir = os.path.join(
                        md_dir_path, item_in_md_dir)

                    if os.path.isfile(item_path_in_md_dir):
                        if item_in_md_dir.startswith(file_base_name + '.') and item_in_md_dir.endswith('.md'):
                            potential_parser_name = item_in_md_dir[len(
                                file_base_name)+1: -len('.md')]
                            if potential_parser_name and potential_parser_name != 'marker' and potential_parser_name not in parsers:
                                parsers.append(potential_parser_name)

            default_parser = ''
            parser_hierarchy = ['docling', 'marker',
                                'llamaparse', 'pdfplumber']
            if parsers:
                for p_hier in parser_hierarchy:
                    if p_hier in parsers:
                        default_parser = p_hier
                        break
                if not default_parser and parsers:
                    default_parser = parsers[0]

            index_data['files'].append({
                'name': file_name,
                'size': file_size,
                'hash': file_hash,
                'parsers': {
                    'det': parsers if parsers else [],
                    'default': default_parser,
                    'status': ''
                }
            })

    # Process directories (using the pre-filtered sub_dir_names)
    for dir_name in sub_dir_names:
        # Ensure dir_name itself is not hidden (already done by caller, but good for safety if used elsewhere)
        # if dir_name.startswith('.') or dir_name.startswith('_') or dir_name == 'md':
        #     continue
        dir_path = os.path.join(current_root, dir_name)
        dir_size = 0
        try:
            # Calculate size only for files directly within the subdirectory
            dir_size = sum(os.path.getsize(os.path.join(dir_path, f)) for f in os.listdir(
                dir_path) if os.path.isfile(os.path.join(dir_path, f)))
            dir_hash = hashlib.md5(
                str(sorted(os.listdir(dir_path))).encode()).hexdigest()
        except FileNotFoundError:  # Handle case where directory might be removed during processing
            print(
                f"Warning: Directory {dir_path} not found during size/hash calculation.")
            dir_hash = ''  # Or some other placeholder

        index_data['directories'].append({
            'name': dir_name,
            'size': dir_size,
            'hash': dir_hash,
            'parser': ''  # Directories don't have parsers
        })
    return index_data


# Helper function to compare index data and print changes
def _compare_and_print_index_changes(old_data: Optional[Dict], new_data: Dict, index_file_path: str, test_mode: bool = False):
    """Compares old and new index data and prints changes verbosely.

    Args:
        old_data: The old index data dictionary, or None if no old index existed.
        new_data: The new index data dictionary.
        index_file_path: Path to the index file for context in messages.
    """
    if old_data is None:
        print(f"Index created: {index_file_path}")
        if not new_data.get('files') and not new_data.get('directories'):
            print(f"  (Index is empty)")
        for file_entry in new_data.get('files', []):
            print(
                f"  + Added file: {file_entry['name']} (size: {file_entry['size']}, hash: {file_entry['hash'][:7]}..., parsers: {file_entry['parsers']['default'] or 'None'})")
        for dir_entry in new_data.get('directories', []):
            print(
                f"  + Added directory: {dir_entry['name']} (size: {dir_entry['size']}, hash: {dir_entry['hash'][:7]}...)")
        return

    old_files_map = {f['name']: f for f in old_data.get('files', [])}
    new_files_map = {f['name']: f for f in new_data.get('files', [])}

    old_dirs_map = {d['name']: d for d in old_data.get('directories', [])}
    new_dirs_map = {d['name']: d for d in new_data.get('directories', [])}

    # Determine if significant changes occurred to warrant the "Updating index" header
    changes_made_for_header = False

    # Check for file changes (additions, removals, modifications)
    for name, new_file_meta in new_files_map.items():
        if name not in old_files_map:
            changes_made_for_header = True
            break
        else:
            old_file_meta = old_files_map[name]
            if (old_file_meta['size'] != new_file_meta['size'] or
                old_file_meta['hash'] != new_file_meta['hash'] or
                    old_file_meta['parsers'] != new_file_meta['parsers']):
                changes_made_for_header = True
                break
    if not changes_made_for_header:
        for name in old_files_map:
            if name not in new_files_map:
                changes_made_for_header = True
                break

    # Check for directory changes (additions, removals, significant modifications)
    if not changes_made_for_header:
        for name, new_dir_meta in new_dirs_map.items():
            if name not in old_dirs_map:
                changes_made_for_header = True
                break
            else:
                old_dir_meta = old_dirs_map[name]
                # Check for hash change or significant size change (more than 1 byte difference)
                if (old_dir_meta['hash'] != new_dir_meta['hash'] or
                        abs(old_dir_meta['size'] - new_dir_meta['size']) > 1):
                    changes_made_for_header = True
                    break
    if not changes_made_for_header:
        for name in old_dirs_map:
            if name not in new_dirs_map:
                changes_made_for_header = True
                break

    # Print update message only if significant changes were detected
    if changes_made_for_header:
        print(f"Updating index: {index_file_path}")

    # Flag to track if any changes were printed in the detailed section
    changes_made = False

    # File changes
    for name, new_file_meta in new_files_map.items():
        if name not in old_files_map:
            print(
                f"  + Added file: {name} (size: {new_file_meta['size']}, hash: {new_file_meta['hash'][:7]}..., parsers: {new_file_meta['parsers']['default'] or 'None'})")
            changes_made = True
        else:
            old_file_meta = old_files_map[name]
            diffs = []
            if old_file_meta['size'] != new_file_meta['size']:
                diffs.append(
                    f"size ({old_file_meta['size']} -> {new_file_meta['size']})")
            if old_file_meta['hash'] != new_file_meta['hash']:
                diffs.append(
                    f"hash ({old_file_meta['hash'][:7]}... -> {new_file_meta['hash'][:7]}...)")
            if old_file_meta['parsers'] != new_file_meta['parsers']:
                old_parsers_info = old_file_meta['parsers']
                new_parsers_info = new_file_meta['parsers']
                parser_diff_parts = []

                # Check default parser change
                if old_parsers_info.get('default', '') != new_parsers_info.get('default', ''):
                    parser_diff_parts.append(
                        f"default: '{old_parsers_info.get('default', '') or 'None'}' -> '{new_parsers_info.get('default', '') or 'None'}'"
                    )

                # Check detected parsers changes
                old_det_set = set(old_parsers_info.get('det', []))
                new_det_set = set(new_parsers_info.get('det', []))

                added_parsers = sorted(list(new_det_set - old_det_set))
                removed_parsers = sorted(list(old_det_set - new_det_set))

                if added_parsers:
                    parser_diff_parts.append(
                        f"detected_added: {', '.join(added_parsers)}")
                if removed_parsers:
                    parser_diff_parts.append(
                        f"detected_removed: {', '.join(removed_parsers)}")

                # Check status change
                if old_parsers_info.get('status', '') != new_parsers_info.get('status', ''):
                    parser_diff_parts.append(
                        f"status: '{old_parsers_info.get('status', '')}' -> '{new_parsers_info.get('status', '')}'"
                    )

                if parser_diff_parts:  # Only add to diffs if there are actual parser changes to report
                    diffs.append(f"parsers ({'; '.join(parser_diff_parts)})")
            if diffs:
                print(f"  ~ Modified file: {name} ({', '.join(diffs)})")
                changes_made = True

    for name in old_files_map:
        if name not in new_files_map:
            print(f"  - Removed file: {name}")
            changes_made = True

    # Directory changes
    for name, new_dir_meta in new_dirs_map.items():
        if name not in old_dirs_map:
            print(
                f"  + Added directory: {name} (size: {new_dir_meta['size']}, hash: {new_dir_meta['hash'][:7]}...)")
            changes_made = True
        else:
            old_dir_meta = old_dirs_map[name]
            diffs = []
            size_changed_significantly = False  # Tracks if size changed by more than 1 byte
            hash_changed = old_dir_meta['hash'] != new_dir_meta['hash']

            if old_dir_meta['size'] != new_dir_meta['size']:
                size_diff_val = abs(
                    old_dir_meta['size'] - new_dir_meta['size'])
                diffs.append(
                    f"size ({old_dir_meta['size']} -> {new_dir_meta['size']})")
                if size_diff_val > 1:
                    size_changed_significantly = True

            if hash_changed:
                diffs.append(
                    f"hash ({old_dir_meta['hash'][:7]}... -> {new_dir_meta['hash'][:7]}...)")

                # Determine if we should print a modification message.
                # Print if hash changed OR if size changed significantly (by more than 1 byte).
                # Do not print if only size changed by 1 byte or less and hash remained the same.
                if hash_changed or size_changed_significantly:
                    message = f"  ~ Modified directory: {name} ({', '.join(diffs)})"
                    # Add specific note if only size changed significantly (hash is the same)
                    if not hash_changed and size_changed_significantly:
                        message += " (likely due to content changes within files in this directory)"
                    print(message)
                    changes_made = True

    for name in old_dirs_map:
        if name not in new_dirs_map:
            print(f"  - Removed directory: {name}")
            changes_made = True

    # Skip printing message if only timestamp changed and no other changes
    if not changes_made and not test_mode:  # Ensure header is printed in test_mode even if no changes
        return
    if test_mode and not changes_made_for_header and not changes_made:
        # If in test mode and no changes were found, explicitly state that for this index file.
        print(f"[TEST MODE] No changes detected for index: {index_file_path}")
        return


def create_index(directory: str, recursive: bool = False, test_mode: bool = False) -> None:
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

                    # 1b. Check for md/<basename>.md (plain md file, treat as parser "md")
                    plain_md_file_path = os.path.join(
                        md_dir_path, file_base_name + ".md")
                    if os.path.isfile(plain_md_file_path) and 'md' not in parsers:
                        parsers.append('md')

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

                # Determine default parser based on hierarchy
                default_parser = ''
                parser_hierarchy = ['docling', 'marker',
                                    'llamaparse', 'pdfplumber']
                if parsers:
                    for p_hier in parser_hierarchy:
                        if p_hier in parsers:
                            default_parser = p_hier
                            break
                    if not default_parser and parsers:  # if no hierarchy match, pick first available
                        default_parser = parsers[0]

                index_data['files'].append({
                    'name': file,
                    'size': file_size,
                    'hash': file_hash,
                    'parsers': {
                        'det': parsers if parsers else [],
                        'default': default_parser,
                        'status': ''
                    }
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
            json.dump(index_data, f, indent=4)  # Added indent for readability

        # Verbose output is now handled by _compare_and_print_index_changes or directly in update_index for new creations.
        # For create_index, we can assume it's a fresh creation, so a simple message is fine,
        # or rely on update_index to call _compare_and_print_index_changes with old_data=None.
        # To avoid duplicate printing if create_index is called from update_index,
        # we'll let update_index handle the verbose output.
        # However, if create_index is called directly, it should still be verbose.
        # The current _compare_and_print_index_changes handles the old_data=None case well.

        # If create_index is called directly (not from update_index), it should print changes.
        # We can simulate this by calling _compare_and_print_index_changes with old_data=None.
        # This check `__name__ == '__main__'` is a placeholder for a more robust way to detect direct call context if needed.
        # For now, let's assume direct calls to create_index should be verbose.
        if not test_mode:
            with open(index_path, 'w') as f:
                json.dump(index_data, f, indent=4)
        else:
            print(
                f"[TEST MODE] Would create index (not writing): {index_path}")
        _compare_and_print_index_changes(
            None, index_data, index_path, test_mode=test_mode)

        if not recursive:
            break


def update_index(directory: str, max_age: int = 5, recursive: bool = False, test_mode: bool = False) -> None:
    """Update existing index files if they're older than max_age seconds.

    Args:
        directory: Root directory to update indexes in
        max_age: Maximum age (in seconds) before index is considered stale
        recursive: Whether to process subdirectories recursively
    """
    for root, dirs, files_in_root in os.walk(directory):
        # Skip hidden directories, ./md subdirs, and directories starting with '_'
        filtered_sub_dirs = [d for d in dirs if not d.startswith(
            '.') and not d.startswith('_') and d != 'md']
        dirs[:] = filtered_sub_dirs  # Modify dirs in place for os.walk

        config = ConfigManager()
        index_file_name = config.get('index_file_name')
        index_path = os.path.join(root, index_file_name)

        old_index_data: Optional[Dict] = None
        needs_update = True

        if os.path.exists(index_path):
            index_age = time.time() - os.path.getmtime(index_path)
            if index_age <= max_age and not test_mode:  # In test_mode, always proceed to check for changes
                print(
                    f"Index is up-to-date: {index_path} (age: {index_age:.2f}s)")
                needs_update = False
            else:
                try:
                    with open(index_path, 'r') as f:
                        old_index_data = json.load(f)
                except json.JSONDecodeError:
                    print(
                        f"  Warning: Could not read old index file {index_path}. Will create a new one.")
                    old_index_data = None
                except Exception as e:
                    print(
                        f"  Warning: Error reading old index file {index_path}: {e}. Will create a new one.")
                    old_index_data = None
        else:
            # This message will be effectively shown by _compare_and_print_index_changes when old_data is None
            # print(f"Index file not found, will create: {index_path}")
            old_index_data = None  # Ensure old_index_data is None if file not found

        if not needs_update and not test_mode:
            if not recursive:
                break
            continue

        # Generate new index data
        new_index_data = _generate_index_data_for_path(
            root, filtered_sub_dirs, files_in_root)

        # Compare and print changes
        _compare_and_print_index_changes(
            old_index_data, new_index_data, index_path, test_mode=test_mode)

        # Write the new index file only if not in test_mode
        if not test_mode:
            try:
                with open(index_path, 'w') as f:
                    json.dump(new_index_data, f, indent=4)
            except IOError as e:
                print(f"  Error writing index file {index_path}: {e}")
        # else:
            # If in test_mode, the _compare_and_print_index_changes function already indicates actions.
            # print(f"[TEST MODE] Would update/create index (not writing): {index_path}")

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
