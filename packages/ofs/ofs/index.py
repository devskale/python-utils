"""Index management functionality for OFS.

This module provides index creation, update, and clear operations
for OFS directory structures, adapted from pdf2md indexing.
"""

import os
import time
import json
import hashlib
import unicodedata
from pathlib import Path
from typing import Optional, Dict, List, Any
from .config import get_config
from .index_helper import _has_content_changes
from .logging import setup_logger

# Module logger
logger = setup_logger(__name__)

# Relevant file extensions for OFS indexing
RELEVANT_EXTENSIONS = ['.pdf', '.docx', '.xlsx', '.pptx', '.jpg', '.jpeg', '.png', '.gif']


def _generate_index_data_for_path(
    current_root: str, 
    sub_dir_names: List[str], 
    files_in_current_root: List[str], 
    existing_index_path: Optional[str] = None
) -> Dict:
    """Generate index data for a given path.
    
    Args:
        current_root: The root directory path
        sub_dir_names: List of subdirectory names
        files_in_current_root: List of files in the current root
        existing_index_path: Path to existing index file for comparison
        
    Returns:
        Dictionary containing index data
    """
    config = get_config()
    # Use configurable index file name
    index_file_name = config.get('INDEX_FILE', 'ofs.index.json')
    
    # Load existing index data if available
    existing_data = None
    if existing_index_path and os.path.exists(existing_index_path):
        try:
            with open(existing_index_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except (IOError, json.JSONDecodeError, PermissionError) as e:
            logger.warning(f"Could not load existing index from {existing_index_path}: {e}")
            existing_data = {}
    
    # Create index data structure
    index_data = {
        "timestamp": int(time.time()),
        "directories": [],
        "files": []
    }
    
    # Process directories
    for dir_name in sub_dir_names:
        dir_path = os.path.join(current_root, dir_name)
        if os.path.exists(dir_path):
            dir_stat = os.stat(dir_path)
            dir_info = {
                "name": dir_name,
                "size": dir_stat.st_size,
                "modified": int(dir_stat.st_mtime),
                "hash": _calculate_directory_hash(dir_path)
            }
            index_data["directories"].append(dir_info)
    
    # Process files
    for file_name in files_in_current_root:
        file_path = os.path.join(current_root, file_name)
        if os.path.exists(file_path):
            file_stat = os.stat(file_path)
            # Detect available parsers by scanning md directory
            parsers = []
            default_parser = ''
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
            
            # Determine default parser based on hierarchy
            parser_hierarchy = ['docling', 'marker', 'llamaparse', 'pdfplumber']
            if parsers:
                for p_hier in parser_hierarchy:
                    if p_hier in parsers:
                        default_parser = p_hier
                        break
                if not default_parser and parsers:
                    default_parser = parsers[0]
            
            file_info = {
                "name": file_name,
                "size": file_stat.st_size,
                "modified": int(file_stat.st_mtime),
                "hash": _calculate_file_hash(file_path),
                "extension": os.path.splitext(file_name)[1].lower(),
                "parsers": {
                    "det": parsers if parsers else [],
                    "default": default_parser,
                    "status": ""
                },
                "meta": {}
            }
            
            # Preserve existing meta data if available
            if existing_data:
                existing_file = next(
                    (f for f in existing_data.get('files', []) if f['name'] == file_name), 
                    None
                )
                if existing_file:
                    file_info['meta'] = existing_file.get('meta', {})
            
            index_data["files"].append(file_info)
    
    return index_data


def _calculate_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        SHA-256 hash as hexadecimal string
    """
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except (IOError, OSError):
        return ""


def _calculate_directory_hash(dir_path: str) -> str:
    """Calculate hash based on directory contents.
    
    Args:
        dir_path: Path to the directory
        
    Returns:
        Hash based on directory structure and file names
    """
    hash_sha256 = hashlib.sha256()
    try:
        for item in sorted(os.listdir(dir_path)):
            hash_sha256.update(item.encode('utf-8'))
        return hash_sha256.hexdigest()
    except (IOError, OSError):
        return ""


def filter_directories(dirs: List[str]) -> List[str]:
    """Filter out hidden directories and specific subdirectories.
    
    Args:
        dirs: List of directory names
        
    Returns:
        Filtered list of directory names
    """
    return [d for d in dirs if not d.startswith('.') and d != 'md' and d != 'archive']


def filter_files(files: List[str]) -> List[str]:
    """Filter out hidden files and irrelevant extensions.
    
    Args:
        files: List of file names
        
    Returns:
        Filtered list of file names
    """
    return [f for f in files if not f.startswith('.') and os.path.splitext(f)[1].lower() in RELEVANT_EXTENSIONS]


def read_index_file(path: str) -> Optional[Dict]:
    """Read and return index data from a file.
    
    Args:
        path: Path to the index file
        
    Returns:
        Index data dictionary or None if file doesn't exist
    """
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return None
    return None


def write_index_file(path: str, data: Dict) -> None:
    """Write index data to a file.
    
    Args:
        path: Path to write the index file
        data: Index data dictionary
    """
    try:
        # Ensure directory exists before writing
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except (IOError, OSError, PermissionError) as e:
        logger.error(f"Error writing index file {path}: {e}")
        raise


def traverse_directories(directory: str, recursive: bool = False):
    """Traverse directories with filtering.
    
    Args:
        directory: Root directory to traverse
        recursive: Whether to traverse recursively
        
    Yields:
        Tuple of (root, dirs, files) for each directory
    """
    for root, dirs, files in os.walk(directory):
        dirs[:] = filter_directories(dirs)  # Filter directories in place
        yield root, dirs, filter_files(files)
        if not recursive:
            break


def create_index(directory: str, recursive: bool = False, force: bool = False) -> bool:
    """Create index files for the specified directory.
    
    Args:
        directory: Directory to index
        recursive: Whether to create indexes recursively
        force: Whether to overwrite existing index files
        
    Returns:
        True if successful, False otherwise
    """
    config = get_config()
    # Use configurable index file name
    index_file_name = config.get('INDEX_FILE', 'ofs.index.json')
    
    try:
        for root, dirs, files in traverse_directories(directory, recursive):
            index_path = os.path.join(root, index_file_name)
            
            # Skip if index exists and force is False
            if os.path.exists(index_path) and not force:
                logger.info(f"Index already exists: {index_path} (use --force to overwrite)")
                continue
            
            # Generate index data
            index_data = _generate_index_data_for_path(root, dirs, files)
            
            # Write index file
            write_index_file(index_path, index_data)
            logger.info(f"Created index: {index_path}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating index: {e}")
        return False


def update_index(directory: str, recursive: bool = False, max_age_hours: int = 24) -> bool:
    """Update existing index files if they are outdated or content has changed.
    
    Args:
        directory: Directory to update indexes for
        recursive: Whether to update indexes recursively
        max_age_hours: Maximum age in hours before forcing update
        
    Returns:
        True if successful, False otherwise
    """
    # Load configuration and use configurable index file name
    config = get_config()
    index_file_name = config.get('INDEX_FILE', 'ofs.index.json')
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    try:
        updated_any = False
        for root, dirs, files in traverse_directories(directory, recursive):
            index_path = os.path.join(root, index_file_name)
            
            # If no index exists, create one
            if not os.path.exists(index_path):
                # Generate new index data
                index_data = _generate_index_data_for_path(root, dirs, files, index_path)
                write_index_file(index_path, index_data)
                rel_path = os.path.relpath(root, directory)
                logger.info(f"Created index for {rel_path}")
                updated_any = True
                continue
            
            # Check if index is too old
            index_stat = os.stat(index_path)
            age_seconds = current_time - index_stat.st_mtime
            
            if age_seconds > max_age_seconds:
                logger.info(f"Index too old ({age_seconds/3600:.1f}h), updating: {index_path}")
                # Generate new index data
                index_data = _generate_index_data_for_path(root, dirs, files, index_path)
                write_index_file(index_path, index_data)
                updated_any = True
                continue
            
            # Check for content changes
            existing_data = read_index_file(index_path)
            new_data = _generate_index_data_for_path(root, dirs, files, index_path)
            
            if _has_content_changes(existing_data, new_data, root):
                # Show relative path from the base directory
                rel_path = os.path.relpath(root, directory)
                logger.info(f"Content changes {rel_path}")
                write_index_file(index_path, new_data)
                updated_any = True
            # Skip printing "Index up to date" messages
        
        return True
    except Exception as e:
        logger.error(f"Error updating index: {e}")
        return False


def clear_index(directory: str, recursive: bool = False) -> bool:
    """Remove index files from the specified directory.
    
    Args:
        directory: Directory to clear indexes from
        recursive: Whether to clear indexes recursively
        
    Returns:
        True if successful, False otherwise
    """
    config = get_config()
    # Use pdf2md compatible index file name for compatibility
    config = get_config()
    index_file_name = config.get('INDEX_FILE', 'ofs.index.json')
    
    try:
        for root, dirs, files in traverse_directories(directory, recursive):
            index_path = os.path.join(root, index_file_name)
            
            if os.path.exists(index_path):
                os.remove(index_path)
                logger.info(f"Removed index: {index_path}")
            else:
                logger.info(f"No index found: {index_path}")
        
        return True
    except Exception as e:
        logger.error(f"Error clearing index: {e}")
        return False


def load_index_from_directory(directory: str) -> Optional[Dict]:
    """Load index data from a directory.
    
    Args:
        directory: Directory containing the index file
        
    Returns:
        Dictionary with index data, or None if index file not found
    """
    config = get_config()
    # Use configurable index file name
    index_file_name = config.get('INDEX_FILE', 'ofs.index.json')
    index_path = os.path.join(directory, index_file_name)
    return read_index_file(index_path)


def process_index_file(index_path: str) -> tuple[int, int, int]:
    """Process an index file and return counts for documents, parsers, and categories.
    
    Args:
        index_path: Path to the index file
        
    Returns:
        A tuple containing:
        - Total number of documents
        - Number of parsed documents (with markdown files in /md subdirectory)
        - Number of categorized documents (with non-empty meta.kategorie or meta.Kategorie)
    """
    if not os.path.exists(index_path):
        return 0, 0, 0
    
    index_data = read_index_file(index_path)
    if not index_data:
        return 0, 0, 0
    
    # Get the directory containing the index file to check for md/ subdirectory
    index_dir = os.path.dirname(index_path)
    md_dir = os.path.join(index_dir, 'md')
    
    total_docs = len(index_data.get('files', []))
    parsed_docs = 0
    categorized_docs = 0
    
    for file_entry in index_data.get('files', []):
        # Check if document has been parsed by looking for markdown files in md/ directory
        file_name = file_entry.get('name', '')
        if file_name and os.path.exists(md_dir):
            # Look for any markdown file that starts with the base filename
            base_name = os.path.splitext(file_name)[0]
            md_files = [f for f in os.listdir(md_dir) if f.startswith(base_name) and f.endswith('.md')]
            if md_files:
                parsed_docs += 1
        
        # Check for both "kategorie" and "Kategorie" (case variations)
        meta = file_entry.get('meta', {})
        if meta.get('kategorie') or meta.get('Kategorie'):
            categorized_docs += 1
    
    return total_docs, parsed_docs, categorized_docs


def print_index_stats(root_dir: str) -> None:
    """Print statistics for indexed files and directories with detailed bieter information.
    
    Args:
        root_dir: Root directory to analyze
    """
    config = get_config()
    # Use pdf2md compatible index file name for compatibility
    index_file_name = '.pdf2md_index.json'
    results = []
    
    for entry in os.listdir(root_dir):
        if entry.startswith('.') or entry == 'archive':
            continue
        
        entry_path = os.path.join(root_dir, entry)
        if not os.path.isdir(entry_path):
            continue
        
        # Process A directory
        a_dir_path = os.path.join(entry_path, 'A')
        a_docs, a_parsers, a_categories = 0, 0, 0
        if os.path.exists(a_dir_path):
            index_path = os.path.join(a_dir_path, index_file_name)
            a_docs, a_parsers, a_categories = process_index_file(index_path)
        
        # Process B directory and collect bieter information
        b_dir_path = os.path.join(entry_path, 'B')
        bieter_list = []
        total_b_docs, total_b_parsers, total_b_categories = 0, 0, 0
        
        if os.path.exists(b_dir_path):
            for bieter_name in os.listdir(b_dir_path):
                if bieter_name.startswith('.') or bieter_name == 'archive':
                    continue
                
                bieter_path = os.path.join(b_dir_path, bieter_name)
                if os.path.isdir(bieter_path):
                    index_path = os.path.join(bieter_path, index_file_name)
                    b_docs, b_parsers, b_categories = process_index_file(index_path)
                    
                    if b_docs > 0:  # Only include bieters with documents
                        bieter_list.append({
                            'name': bieter_name,
                            'docs': b_docs,
                            'parsers': b_parsers,
                            'categories': b_categories
                        })
                        total_b_docs += b_docs
                        total_b_parsers += b_parsers
                        total_b_categories += b_categories
        
        # Calculate totals
        total_docs = a_docs + total_b_docs
        total_parsers = a_parsers + total_b_parsers
        total_categories = a_categories + total_b_categories
        
        if total_docs > 0:
            results.append({
                'project': entry,
                'total_docs': total_docs,
                'parsed_docs': total_parsers,
                'categorized_docs': total_categories,
                'a_docs': a_docs,
                'b_docs': total_b_docs,
                'bieter_list': bieter_list
            })
    
    # Print results in tree format similar to pdf2md
    if results:
        logger.info(f"Showing stats for indexes in {root_dir}")
        for result in results:
            logger.info(f"{result['project']} ({result['total_docs']} docs, {result['parsed_docs']} pars, {result['categorized_docs']} kat)")
            
            # Show bieter information if available
            if result['bieter_list']:
                for i, bieter in enumerate(result['bieter_list']):
                    prefix = "   ├─" if i < len(result['bieter_list']) - 1 else "   └─"
                    logger.info(f"{prefix} {bieter['name']} ({bieter['docs']} docs, {bieter['parsers']} pars, {bieter['categories']} kat)")
    else:
        logger.info("No indexed projects found.")


def generate_un_items_list(input_path: str, output_file: str = None, json_output: bool = False, recursive: bool = True) -> None:
    """
    Generate a list of unparsed and uncategorized files in OFS structure.
    
    This function identifies files that lack corresponding Markdown files or category metadata
    within the OFS (Opinionated File System) structure. It looks for:
    - Files without corresponding .md files in the md/ directory
    - Files without category metadata in kriterien.meta.json
    
    Args:
        input_path: Path to the OFS directory or file to analyze
        output_file: Optional output file path. If None, prints to stdout
        json_output: Whether to output in JSON format (default: False for plain text)
        recursive: Whether to process subdirectories recursively (default: True)
    """
    # Imports moved to top of file
    
    def is_ofs_directory(path: Path) -> bool:
        """Check if a directory follows OFS structure."""
        return (path / 'projekt.meta.json').exists() or (path / 'md').exists()
    
    def get_markdown_files(md_dir: Path) -> set:
        """Get set of base filenames that have corresponding markdown files."""
        markdown_files = set()
        if md_dir.exists():
            for md_file in md_dir.rglob('*.md'):
                # Extract original filename from markdown filename
                # Handle patterns like: filename.processor.md, filename/filename.processor.md
                md_name = md_file.stem
                
                # Check if this is a processor-specific markdown file
                # Common processors: docling, llamaparse, marker, pdfplumber
                processors = ['docling', 'llamaparse', 'marker', 'pdfplumber']
                
                base_name = None
                for processor in processors:
                    if md_name.endswith(f'.{processor}'):
                        # Remove .processor suffix to get base filename
                        base_name = md_name[:-len(f'.{processor}')]
                        break
                
                if base_name is None:
                    # Fallback: if no processor suffix found, use the whole stem
                    # This handles cases like filename.md or other patterns
                    base_name = md_name
                
                if base_name:
                    markdown_files.add(base_name)
        return markdown_files
    
    def get_categorized_files(kriterien_file: Path, directory: Path = None) -> set:
        """Get set of filenames that have category metadata.
        
        Checks both kriterien.meta.json and local .ofs.index.json files
        for categorization metadata.
        
        Args:
            kriterien_file: Path to kriterien.meta.json file
            directory: Directory to check for local .ofs.index.json files
        
        Returns:
            Set of base filenames that have categorization metadata
        """
        categorized_files = set()
        
        # Check kriterien.meta.json file
        if kriterien_file.exists():
            try:
                with open(kriterien_file, 'r', encoding='utf-8') as f:
                    kriterien_data = json.load(f)
                    
                # Extract filenames from kriterien structure
                for category, items in kriterien_data.get('kriterien', {}).items():
                    if isinstance(items, dict):
                        for filename in items.keys():
                            # Remove file extension for comparison
                            base_name = Path(filename).stem
                            categorized_files.add(base_name)
            except (IOError, json.JSONDecodeError, PermissionError) as e:
                logger.warning(f"Could not load kriterien file {kriterien_file}: {e}")
        
        # Check local .ofs.index.json files for meta.kategorie
        if directory:
            config = get_config()
            index_file = directory / config.get('INDEX_FILE', '.ofs.index.json')
            if index_file.exists():
                try:
                    with open(index_file, 'r', encoding='utf-8') as f:
                        index_data = json.load(f)
                        
                    # Check each file entry for meta.kategorie
                    for file_entry in index_data.get('files', []):
                        meta = file_entry.get('meta', {})
                        if meta.get('kategorie'):
                            # Remove file extension for comparison
                            filename = file_entry.get('name', '')
                            if filename:
                                base_name = Path(filename).stem
                                categorized_files.add(base_name)
                except (IOError, json.JSONDecodeError, PermissionError) as e:
                    logger.warning(f"Could not load index file {index_file}: {e}")
        
        return categorized_files
    
    def find_unparsed_files(directory: Path, base_path: Path = None) -> List[Dict[str, Any]]:
        """Find files that are unparsed or uncategorized in an OFS directory.
        
        Args:
            directory: The OFS project directory to scan
            base_path: The base path for calculating relative paths (defaults to directory)
        """
        unparsed_files = []
        
        if not is_ofs_directory(directory):
            return unparsed_files
        
        # Use directory as base_path if not provided (for single directory scans)
        if base_path is None:
            base_path = directory
        
        # Get global categorized files from project root
        kriterien_file = directory / 'kriterien.meta.json'
        categorized_files = get_categorized_files(kriterien_file, directory)
        
        # Check A and B directories for unparsed files
        for subdir_name in ['A', 'B']:
            subdir = directory / subdir_name
            if subdir.exists() and subdir.is_dir():
                # For B directory, check each bieter subdirectory
                if subdir_name == 'B':
                    for bieter_dir in subdir.iterdir():
                        if bieter_dir.is_dir():
                            # Get markdown files specific to this bieter directory
                            bieter_md_dir = bieter_dir / 'md'
                            markdown_files = get_markdown_files(bieter_md_dir)
                            
                            # Get categorized files including local index for this bieter directory
                            bieter_categorized_files = get_categorized_files(kriterien_file, bieter_dir)
                            
                            for file_path in bieter_dir.rglob('*'):
                                if file_path.is_file() and not file_path.name.startswith('.'):
                                    # Skip md directory files
                                    if 'md' in file_path.parts:
                                        continue
                                        
                                    # Only process files with relevant extensions
                                    if file_path.suffix.lower() not in RELEVANT_EXTENSIONS:
                                        continue
                                        
                                    base_name = file_path.stem
                                    relative_path = file_path.relative_to(base_path)
                                    
                                    # Check if file is unparsed or uncategorized
                                    is_unparsed = base_name not in markdown_files
                                    is_uncategorized = base_name not in bieter_categorized_files
                                    
                                    if is_unparsed or is_uncategorized:
                                        # Handle filesystem encoding issues by normalizing Unicode
                                        file_path_str = unicodedata.normalize('NFC', str(relative_path)).replace('\\', '/')
                                        bieter_name = unicodedata.normalize('NFC', bieter_dir.name)
                                        
                                        unparsed_files.append({
                                            'file': file_path_str,
                                            'size': file_path.stat().st_size,
                                            'unparsed': is_unparsed,
                                            'uncategorized': is_uncategorized,
                                            'directory': subdir_name,
                                            'bieter': bieter_name
                                        })
                else:
                    # For A directory, get markdown files from A/md/
                    a_md_dir = subdir / 'md'
                    markdown_files = get_markdown_files(a_md_dir)
                    
                    # Get categorized files including local index for A directory
                    a_categorized_files = get_categorized_files(kriterien_file, subdir)
                    
                    # Check files directly in A directory
                    for file_path in subdir.rglob('*'):
                        if file_path.is_file() and not file_path.name.startswith('.'):
                            # Skip md directory files
                            if 'md' in file_path.parts:
                                continue
                                
                            # Only process files with relevant extensions
                            if file_path.suffix.lower() not in RELEVANT_EXTENSIONS:
                                continue
                                
                            base_name = file_path.stem
                            relative_path = file_path.relative_to(base_path)
                            
                            # Check if file is unparsed or uncategorized
                            is_unparsed = base_name not in markdown_files
                            is_uncategorized = base_name not in a_categorized_files
                            
                            if is_unparsed or is_uncategorized:
                                # Handle filesystem encoding issues by normalizing Unicode
                                file_path_str = unicodedata.normalize('NFC', str(relative_path)).replace('\\', '/')
                                
                                unparsed_files.append({
                                    'file': file_path_str,
                                    'size': file_path.stat().st_size,
                                    'unparsed': is_unparsed,
                                    'uncategorized': is_uncategorized,
                                    'directory': subdir_name,
                                    'bieter': None
                                })
        
        return unparsed_files
    
    # Main processing logic
    input_path_obj = Path(input_path)
    all_unparsed_files = []
    
    if input_path_obj.is_file():
        # Handle single file case
        parent_dir = input_path_obj.parent
        if is_ofs_directory(parent_dir):
            # Check if this specific file is unparsed/uncategorized
            md_dir = parent_dir / 'md'
            kriterien_file = parent_dir / 'kriterien.meta.json'
            
            markdown_files = get_markdown_files(md_dir)
            categorized_files = get_categorized_files(kriterien_file)
            
            base_name = input_path_obj.stem
            is_unparsed = base_name not in markdown_files
            is_uncategorized = base_name not in categorized_files
            
            if is_unparsed or is_uncategorized:
                # Only process files with relevant extensions
                if input_path_obj.suffix.lower() not in RELEVANT_EXTENSIONS:
                    return
                    
                relative_path = input_path_obj.relative_to(parent_dir)
                # Handle filesystem encoding issues by normalizing Unicode
                file_path_str = unicodedata.normalize('NFC', str(relative_path))
                
                all_unparsed_files.append({
                    'file': file_path_str,
                    'size': input_path_obj.stat().st_size,
                    'unparsed': is_unparsed,
                    'uncategorized': is_uncategorized,
                    'directory': relative_path.parts[0] if len(relative_path.parts) > 1 else 'root',
                    'bieter': relative_path.parts[1] if len(relative_path.parts) > 2 and relative_path.parts[0] == 'B' else None
                })
    elif input_path_obj.is_dir():
        # Handle directory case
        if recursive:
            # Find all OFS directories recursively
            for root, dirs, files in os.walk(input_path_obj):
                root_path = Path(root)
                if is_ofs_directory(root_path):
                    unparsed_files = find_unparsed_files(root_path, input_path_obj)
                    all_unparsed_files.extend(unparsed_files)
        else:
            # Process only the specified directory
            if is_ofs_directory(input_path_obj):
                all_unparsed_files = find_unparsed_files(input_path_obj)
    
    # Generate output
    if json_output:
        # Count only files that are actually unparsed (not just uncategorized)
        unparsed_count = sum(1 for f in all_unparsed_files if f['unparsed'])
        uncategorized_count = sum(1 for f in all_unparsed_files if f['uncategorized'])
        
        output_data = {
            'summary': {
                'total_unparsed': unparsed_count,
                'total_uncategorized': uncategorized_count,
                'total_size': sum(f['size'] for f in all_unparsed_files),
                'scan_path': str(input_path_obj.relative_to(Path.cwd()) if input_path_obj.is_absolute() else input_path_obj),
                'recursive': recursive
            },
            'files': all_unparsed_files
        }
        output_content = json.dumps(output_data, indent=2, ensure_ascii=False)
    else:
        # Plain text output
        lines = []
        if all_unparsed_files:
            for file_info in all_unparsed_files:
                status_parts = []
                if file_info['unparsed']:
                    status_parts.append('unparsed')
                if file_info['uncategorized']:
                    status_parts.append('uncategorized')
                status = ', '.join(status_parts)
                
                size_mb = file_info['size'] / (1024 * 1024)
                bieter_info = f" (bieter: {file_info['bieter']})" if file_info['bieter'] else ""
                lines.append(f"{file_info['file']} - {status} ({size_mb:.2f} MB){bieter_info}")
        # Remove the "No files found" message for less verbosity
        
        output_content = '\n'.join(lines)
    
    # Write output
    if output_file:
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                if json_output:
                    json.dump(output_data, f, indent=4, ensure_ascii=False)
                else:
                    f.write(output_content)
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"Error writing output file {output_file}: {e}")
            raise
    else:
        # Auto-save output to the target directory when no output file specified
        if json_output:
            default_output_file = input_path_obj / 'un_items.json'
        else:
            default_output_file = input_path_obj / 'un_items.txt'
        try:
            os.makedirs(os.path.dirname(default_output_file), exist_ok=True)
            with open(default_output_file, 'w', encoding='utf-8') as f:
                if json_output:
                    json.dump(output_data, f, indent=4, ensure_ascii=False)
                else:
                    f.write(output_content)
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"Error writing default output file {default_output_file}: {e}")
            raise
    # Suppress all stdout output - no printing to console