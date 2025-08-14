"""Helper functions for OFS index management.

This module provides utility functions for index operations,
particularly for detecting content changes between index versions.
"""

from typing import Optional, Dict


def _has_content_changes(old_data: Optional[Dict], new_data: Dict, debug_path: str = "") -> bool:
    """Check if there are actual content changes between old and new index data.
    
    Args:
        old_data: The old index data dictionary, or None if no old index existed
        new_data: The new index data dictionary
        debug_path: Optional path for debug logging
        
    Returns:
        True if there are content changes, False otherwise
    """
    if old_data is None:
        return True
        
    # Compare files
    old_files_map = {f['name']: f for f in old_data.get('files', [])}
    new_files_map = {f['name']: f for f in new_data.get('files', [])}
    
    # Check for added or removed files
    old_file_names = set(old_files_map.keys())
    new_file_names = set(new_files_map.keys())
    if old_file_names != new_file_names:
        return True
        
    # Check for file content changes
    for name, new_file_meta in new_files_map.items():
        old_file_meta = old_files_map[name]
        old_size = old_file_meta.get('size')
        new_size = new_file_meta.get('size')
        old_hash = old_file_meta.get('hash')
        new_hash = new_file_meta.get('hash')
        old_parsers = old_file_meta.get('parsers')
        new_parsers = new_file_meta.get('parsers')
        
        if old_size != new_size:
            return True
        if old_hash != new_hash:
            return True
        if old_parsers != new_parsers:
            return True
            
    # Compare directories
    old_dirs_map = {d['name']: d for d in old_data.get('directories', [])}
    new_dirs_map = {d['name']: d for d in new_data.get('directories', [])}
    
    # Check for added or removed directories
    old_dir_names = set(old_dirs_map.keys())
    new_dir_names = set(new_dirs_map.keys())
    if old_dir_names != new_dir_names:
        return True
        
    # Check for directory content changes
    for name, new_dir_meta in new_dirs_map.items():
        old_dir_meta = old_dirs_map[name]
        old_size = old_dir_meta.get('size')
        new_size = new_dir_meta.get('size')
        old_hash = old_dir_meta.get('hash')
        new_hash = new_dir_meta.get('hash')
        
        if old_size != new_size:
            return True
        if old_hash != new_hash:
            return True
            
    return False


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