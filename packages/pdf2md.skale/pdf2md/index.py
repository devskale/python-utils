# index.py - Index management for PDF to Markdown conversion

import os
import time
import json
import hashlib
from typing import Optional, Dict, List  # Added Optional, Dict, List
from .config import ConfigManager

# Define constants for relevant file extensions
RELEVANT_EXTENSIONS = ['.pdf', '.docx', '.xlsx', '.pptx', '.jpg', '.jpeg', '.png', '.gif']

# Helper function to generate index data for a specific path
def _generate_index_data_for_path(current_root: str, sub_dir_names: List[str], files_in_current_root: List[str], existing_index_path: Optional[str] = None) -> Dict:
    """Generates index data for a specific path, its files, and subdirectories.

    Args:
        current_root: The current directory path being processed.
        sub_dir_names: List of filtered subdirectory names within current_root.
        files_in_current_root: List of all file names within current_root.
        existing_index_path: Path to an existing .pdf2md_index.json file to preserve metadata.

    Returns:
        A dictionary containing the index data for the given path.
    """
    # Load existing index data if available
    existing_meta = {}
    if existing_index_path and os.path.exists(existing_index_path):
        with open(existing_index_path, 'r') as f:
            existing_data = json.load(f)
            for file_entry in existing_data.get('files', []):
                existing_meta[file_entry['name']] = file_entry.get('meta', {})

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

            # Preserve existing metadata if available
            meta = existing_meta.get(file_name, {})

            index_data['files'].append({
                'name': file_name,
                'size': file_size,
                'hash': file_hash,
                'parsers': {
                    'det': parsers if parsers else [],
                    'default': default_parser,
                    'status': ''
                },
                'meta': meta  # Add preserved metadata
            })

    # Process directories (using the pre-filtered sub_dir_names)
    for dir_name in sub_dir_names:
        dir_path = os.path.join(current_root, dir_name)
        dir_size = 0
        try:
            dir_size = sum(os.path.getsize(os.path.join(dir_path, f)) for f in os.listdir(
                dir_path) if os.path.isfile(os.path.join(dir_path, f)))
            dir_hash = hashlib.md5(
                str(sorted(os.listdir(dir_path))).encode()).hexdigest()
        except FileNotFoundError:
            print(
                f"Warning: Directory {dir_path} not found during size/hash calculation.")
            dir_hash = ''

        index_data['directories'].append({
            'name': dir_name,
            'size': dir_size,
            'hash': dir_hash,
            'parser': ''
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


# Helper function to filter directories
def filter_directories(dirs: List[str]) -> List[str]:
    """Filter out hidden directories and specific subdirectories."""
    return [d for d in dirs if not d.startswith('.') and d != 'md' and d != 'archive']

# Helper function to filter files
def filter_files(files: List[str]) -> List[str]:
    """Filter out hidden files and irrelevant extensions."""
    return [f for f in files if not f.startswith('.') and os.path.splitext(f)[1].lower() in RELEVANT_EXTENSIONS]

# Helper function to read index file
def read_index_file(path: str) -> Optional[Dict]:
    """Read and return index data from a file."""
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return None

# Helper function to write index file
def write_index_file(path: str, data: Dict) -> None:
    """Write index data to a file."""
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

# Reusable directory traversal function
def traverse_directories(directory: str, recursive: bool = False):
    """Traverse directories with filtering."""
    for root, dirs, files in os.walk(directory):
        dirs[:] = filter_directories(dirs)  # Filter directories in place
        yield root, dirs, filter_files(files)
        if not recursive:
            break

# Create fresh .pdf2md_index.json files in each directory
def create_index(directory: str, recursive: bool = False, test_mode: bool = False) -> None:
    """Create fresh .pdf2md_index.json files in each directory."""
    for root, dirs, files in traverse_directories(directory, recursive):
        index_data = _generate_index_data_for_path(root, dirs, files)
        index_file_name = ConfigManager().get('index_file_name')
        index_path = os.path.join(root, index_file_name)
        if not test_mode:
            write_index_file(index_path, index_data)
        else:
            print(f"[TEST MODE] Would create index (not writing): {index_path}")
        _compare_and_print_index_changes(None, index_data, index_path, test_mode=test_mode)

# Update existing index files if they're older than max_age seconds
def update_index(directory: str, max_age: int = 5, recursive: bool = False, test_mode: bool = False) -> None:
    """Update existing index files if they're older than max_age seconds."""
    for root, dirs, files in traverse_directories(directory, recursive):
        index_file_name = ConfigManager().get('index_file_name')
        index_path = os.path.join(root, index_file_name)
        old_index_data = read_index_file(index_path)
        needs_update = True

        if old_index_data:
            index_age = time.time() - os.path.getmtime(index_path)
            if index_age <= max_age and not test_mode:
                print(f"Index is up-to-date: {index_path} (age: {index_age:.2f}s)")
                needs_update = False

        if needs_update:
            new_index_data = _generate_index_data_for_path(root, dirs, files, index_path)
            _compare_and_print_index_changes(old_index_data, new_index_data, index_path, test_mode=test_mode)
            if not test_mode:
                write_index_file(index_path, new_index_data)

# Remove all .pdf2md_index.json files
def clear_index(directory: str, recursive: bool = False) -> None:
    """Remove all .pdf2md_index.json files."""
    for root, dirs, _ in traverse_directories(directory, recursive):
        index_file_name = ConfigManager().get('index_file_name')
        index_path = os.path.join(root, index_file_name)
        if os.path.exists(index_path):
            os.remove(index_path)


def get_index_data(directory: str) -> Optional[Dict]:
    """Get index data for a directory.

    Args:
        directory: Path to directory to get index data for

    Returns:
        Dictionary with index data, or None if index file not found
    """
    config = ConfigManager()
    index_file_name = config.get('index_file_name')
    index_path = os.path.join(directory, index_file_name)
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            return json.load(f)
    return None


def process_index_file(index_path: str) -> tuple[int, int, int]:
    """
    Process a .pdf2md_index.json file and return counts for documents, parsers, and categories.

    Args:
        index_path: Path to the .pdf2md_index.json file.

    Returns:
        A tuple containing:
        - Total number of documents.
        - Number of parsed documents (with non-empty parsers.det).
        - Number of categorized documents (with non-empty meta.kategorie or meta.Kategorie).
    """
    if not os.path.exists(index_path):
        return 0, 0, 0

    with open(index_path, 'r') as f:
        index_data = json.load(f)

    total_docs = len(index_data.get('files', []))
    parsed_docs = 0
    categorized_docs = 0

    for file_entry in index_data.get('files', []):
        if file_entry.get('parsers', {}).get('det'):
            parsed_docs += 1
        # Check for both "kategorie" and "Kategorie" (case variations)
        meta = file_entry.get('meta', {})
        if meta.get('kategorie') or meta.get('Kategorie'):
            categorized_docs += 1

    return total_docs, parsed_docs, categorized_docs


# Print stats for indexed files and directories
def print_index_stats(root_dir: str):
    """Print stats for indexed files and directories."""
    config = ConfigManager()
    index_file_name = config.get('index_file_name')
    results = []
    print(f"Debug: Starting to process root directory: {root_dir}")
    for entry in os.listdir(root_dir):
        if entry.startswith('.') or entry == 'archive':
            print(f"Debug: Skipping hidden or archive folder: {entry}")
            continue
        entry_path = os.path.join(root_dir, entry)
        print(f"Debug: Processing entry: {entry}")
        if not os.path.isdir(entry_path):
            print(f"Debug: Skipping non-directory entry: {entry}")
            continue
        # Process A directory
        a_dir_path = os.path.join(entry_path, 'A')
        a_docs, a_parsers, a_categories = 0, 0, 0
        if os.path.exists(a_dir_path):
            index_path = os.path.join(a_dir_path, index_file_name)
            a_docs, a_parsers, a_categories = process_index_file(index_path)
        # Process B directory
        b_dir_path = os.path.join(entry_path, 'B')
        subdirs = []
        if os.path.exists(b_dir_path):
            for d in os.listdir(b_dir_path):
                if d == 'archive':
                    print(f"Debug: Skipping archive folder in B: {d}")
                    continue
                subdir_path = os.path.join(b_dir_path, d)
                if os.path.isdir(subdir_path):
                    index_path = os.path.join(subdir_path, index_file_name)
                    b_docs, b_parsers, b_categories = process_index_file(index_path)
                    subdirs.append((d, b_docs, b_parsers, b_categories))
        results.append((entry, a_docs, a_parsers, a_categories, subdirs))
    # Print results
    print("Debug: Finished processing directories. Preparing results...")
    for project, a_docs, a_parsers, a_categories, subdirs in results:
        print(f"{project} ({a_docs} docs, {a_parsers} pars, {a_categories} kat)")
        for subdir, b_docs, b_parsers, b_categories in subdirs:
            print(f"   ├─ {subdir} ({b_docs} docs, {b_parsers} pars, {b_categories} kat)")


# CLI entry for index stats
if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3 and sys.argv[1] == "--index" and sys.argv[2] == "stats":
        # Usage: python index.py --index stats <root_dir>
        if len(sys.argv) >= 4:
            print_index_stats(sys.argv[3])
        else:
            print("Usage: python index.py --index stats <root_dir>")
            print_index_stats(sys.argv[3])


def generate_unparsed_file_list(directory: str, output_file: str, recursive: bool = False, json_output: bool = False) -> None:
    """
    Generate a list of files without parsed content and save it to a file.

    Args:
        directory: The root directory to scan.
        output_file: Path to the output file where the list will be saved.
        recursive: Whether to scan subdirectories recursively.
        json_output: Whether to output the result in JSON format.
    """
    unparsed_files = []

    for root, dirs, files in traverse_directories(directory, recursive):
        index_file_name = ConfigManager().get('index_file_name')
        index_path = os.path.join(root, index_file_name)

        # Read index data
        index_data = read_index_file(index_path)
        if not index_data:
            print(f"[Warning] No index file found in: {root}. Skipping.")
            continue

        # Identify unparsed files
        for file_entry in index_data.get('files', []):
            if not file_entry.get('parsers', {}).get('det'):  # No parsers detected
                relative_path = os.path.relpath(os.path.join(root, file_entry['name']), directory)
                unparsed_files.append(relative_path)

    # Write unparsed files to the output file
    if unparsed_files:
        if json_output:
            with open(output_file, 'w') as f:
                json.dump({"unparsed_files": unparsed_files}, f, indent=4)
        else:
            with open(output_file, 'w') as f:
                f.write("\n".join(unparsed_files))
        print(f"Found {len(unparsed_files)} unparsed file(s).")
    else:
        print("No unparsed files found.")
        if os.path.exists(output_file):
            os.remove(output_file)  # Remove the output file if it exists and no unparsed files were found.
        if os.path.exists(output_file):
            os.remove(output_file)  # Remove the output file if it exists and no unparsed files were found.

def generate_un_items_list(directory: str, output_file: str, recursive: bool = False, json_output: bool = False) -> None:
    """
    Generate a list of unparsed and uncategorized items and save it to a file.

    Args:
        directory: The root directory to scan.
        output_file: Path to the output file where the list will be saved.
        recursive: Whether to scan subdirectories recursively.
        json_output: Whether to output the result in JSON format.
    """
    un_items = []

    for root, dirs, files in traverse_directories(directory, recursive):
        index_file_name = ConfigManager().get('index_file_name')
        index_path = os.path.join(root, index_file_name)

        # Read index data
        index_data = read_index_file(index_path)
        if not index_data:
            print(f"[Warning] No index file found in: {root}. Skipping.")
            continue

        # Identify unparsed and uncategorized items
        for file_entry in index_data.get('files', []):
            is_unparsed = not file_entry.get('parsers', {}).get('det')  # No parsers detected
            # Check for both "kategorie" and "Kategorie" (case variations)
            meta = file_entry.get('meta', {})
            is_unkategorized = not (meta.get('kategorie') or meta.get('Kategorie'))  # No category metadata
            if is_unparsed or is_unkategorized:
                relative_path = os.path.relpath(os.path.join(root, file_entry['name']), directory)
                un_items.append({
                    "path": relative_path,
                    "unparsed": is_unparsed,
                    "uncategorized": is_unkategorized
                })

    # Write unparsed and uncategorized items to the output file
    if un_items:
        if json_output:
            with open(output_file, 'w') as f:
                json.dump({"un_items": un_items}, f, indent=4)
        else:
            with open(output_file, 'w') as f:
                for item in un_items:
                    f.write(f"{item['path']} (Unparsed: {item['unparsed']}, Uncategorized: {item['uncategorized']})\n")
        print(f"Found {len(un_items)} unparsed or uncategorized item(s).")
    else:
        print("No unparsed or uncategorized items found.")
        if os.path.exists(output_file):
            os.remove(output_file)  # Remove the output file if it exists and no items were found.
