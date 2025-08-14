from typing import Optional, Dict

def _has_content_changes(old_data: Optional[Dict], new_data: Dict, debug_path: str = "") -> bool:
    """Check if there are actual content changes between old and new index data.
    
    Args:
        old_data: The old index data dictionary, or None if no old index existed.
        new_data: The new index data dictionary.
        debug_path: Optional path for debug logging.
        
    Returns:
        True if there are content changes, False otherwise.
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