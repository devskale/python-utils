"""Helper functions for OFS index management.

This module provides utility functions for index operations,
particularly for detecting content changes between index versions.
"""

from typing import Optional, Dict


from typing import Optional, Dict, List, Tuple


def get_detailed_changes(old_data: Optional[Dict], new_data: Dict) -> List[Tuple[str, str, str]]:
    """Get detailed information about changes between old and new index data.
    
    Args:
        old_data: The old index data dictionary, or None if no old index existed
        new_data: The new index data dictionary
        
    Returns:
        List of tuples (item_type, item_name, change_type) where:
        - item_type: 'file' or 'directory'
        - item_name: name of the changed item
        - change_type: 'added', 'removed', 'modified'
    """
    changes = []
    
    if old_data is None:
        # All items are new
        for file_data in new_data.get('files', []):
            changes.append(('file', file_data['name'], 'added'))
        for dir_data in new_data.get('directories', []):
            changes.append(('directory', dir_data['name'], 'added'))
        return changes
        
    # Compare files
    old_files_map = {f['name']: f for f in old_data.get('files', [])}
    new_files_map = {f['name']: f for f in new_data.get('files', [])}
    
    old_file_names = set(old_files_map.keys())
    new_file_names = set(new_files_map.keys())
    
    # Added files
    for name in new_file_names - old_file_names:
        changes.append(('file', name, 'added'))
    
    # Removed files
    for name in old_file_names - new_file_names:
        changes.append(('file', name, 'removed'))
    
    # Modified files
    for name in old_file_names & new_file_names:
        old_file = old_files_map[name]
        new_file = new_files_map[name]
        
        if (old_file.get('size') != new_file.get('size') or
            old_file.get('hash') != new_file.get('hash') or
            old_file.get('parsers') != new_file.get('parsers')):
            changes.append(('file', name, 'modified'))
    
    # Compare directories
    old_dirs_map = {d['name']: d for d in old_data.get('directories', [])}
    new_dirs_map = {d['name']: d for d in new_data.get('directories', [])}
    
    old_dir_names = set(old_dirs_map.keys())
    new_dir_names = set(new_dirs_map.keys())
    
    # Added directories
    for name in new_dir_names - old_dir_names:
        changes.append(('directory', name, 'added'))
    
    # Removed directories
    for name in old_dir_names - new_dir_names:
        changes.append(('directory', name, 'removed'))
    
    # Modified directories
    for name in old_dir_names & new_dir_names:
        old_dir = old_dirs_map[name]
        new_dir = new_dirs_map[name]
        
        if (old_dir.get('size') != new_dir.get('size') or
            old_dir.get('hash') != new_dir.get('hash')):
            changes.append(('directory', name, 'modified'))
    
    return changes


def _has_content_changes(old_data: Optional[Dict], new_data: Dict, debug_path: str = "") -> bool:
    """Check if there are actual content changes between old and new index data.
    
    Args:
        old_data: The old index data dictionary, or None if no old index existed
        new_data: The new index data dictionary
        debug_path: Optional path for debug logging
        
    Returns:
        True if there are content changes, False otherwise
    """
    changes = get_detailed_changes(old_data, new_data)
    return len(changes) > 0


def compare_file_metadata(old_file: Dict, new_file: Dict) -> bool:
    """Compare metadata between two file entries.
    
    Args:
        old_file: Old file metadata dictionary
        new_file: New file metadata dictionary
        
    Returns:
        True if files are different, False if they are the same
    """
    # Compare basic file attributes
    if old_file.get('size') != new_file.get('size'):
        return True
    if old_file.get('hash') != new_file.get('hash'):
        return True
    if old_file.get('modified') != new_file.get('modified'):
        return True
    
    # Compare parser data
    if old_file.get('parsers') != new_file.get('parsers'):
        return True
    
    # Compare metadata
    if old_file.get('meta') != new_file.get('meta'):
        return True
    
    return False


def compare_directory_metadata(old_dir: Dict, new_dir: Dict) -> bool:
    """Compare metadata between two directory entries.
    
    Args:
        old_dir: Old directory metadata dictionary
        new_dir: New directory metadata dictionary
        
    Returns:
        True if directories are different, False if they are the same
    """
    # Compare basic directory attributes
    if old_dir.get('size') != new_dir.get('size'):
        return True
    if old_dir.get('hash') != new_dir.get('hash'):
        return True
    if old_dir.get('modified') != new_dir.get('modified'):
        return True
    
    return False


def validate_index_data(index_data: Dict) -> bool:
    """Validate the structure of index data.
    
    Args:
        index_data: Index data dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(index_data, dict):
        return False
    
    # Check required fields
    required_fields = ['timestamp', 'path', 'directories', 'files']
    for field in required_fields:
        if field not in index_data:
            return False
    
    # Check that directories and files are lists
    if not isinstance(index_data['directories'], list):
        return False
    if not isinstance(index_data['files'], list):
        return False
    
    # Validate file entries
    for file_entry in index_data['files']:
        if not isinstance(file_entry, dict):
            return False
        required_file_fields = ['name', 'path', 'size', 'modified', 'hash']
        for field in required_file_fields:
            if field not in file_entry:
                return False
    
    # Validate directory entries
    for dir_entry in index_data['directories']:
        if not isinstance(dir_entry, dict):
            return False
        required_dir_fields = ['name', 'path', 'size', 'modified', 'hash']
        for field in required_dir_fields:
            if field not in dir_entry:
                return False
    
    return True


def merge_index_metadata(old_data: Dict, new_data: Dict) -> Dict:
    """Merge metadata from old index into new index data.
    
    This preserves parser results and metadata while updating
    file system information.
    
    Args:
        old_data: Old index data dictionary
        new_data: New index data dictionary
        
    Returns:
        Merged index data dictionary
    """
    if not old_data:
        return new_data
    
    # Create maps for efficient lookup
    old_files_map = {f['name']: f for f in old_data.get('files', [])}
    
    # Merge file metadata
    for new_file in new_data.get('files', []):
        file_name = new_file['name']
        if file_name in old_files_map:
            old_file = old_files_map[file_name]
            # Preserve parsers and meta data
            new_file['parsers'] = old_file.get('parsers', {})
            new_file['meta'] = old_file.get('meta', {})
    
    return new_data