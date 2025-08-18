"""
Document listing, metadata handling, and reading for OFS.

This module contains functions for:
- Listing documents for bidders and projects
- Retrieving document details and metadata
- Reading document contents with parser selection
"""

import json
import unicodedata
from pathlib import Path
from typing import Optional, List, Dict, Any

from .config import get_base_dir
from .paths import _load_ofs_index, _search_in_directory


def _collect_bidders_structured(b_dir: Path) -> Dict[str, Any]:
    """
    Collect bidders from B directory, distinguishing between directories and files.
    
    This function orchestrates the collection of bidder data by delegating
    specific tasks to focused helper functions.

    Args:
        b_dir (Path): The B directory to scan

    Returns:
        Dict[str, Any]: Structured data with bidders and files
    """
    if not b_dir.exists():
        return {
            "bidder_directories": [],
            "all_files": [],
            "total_bidders": 0,
            "total_files": 0
        }
    
    # Scan filesystem for bidders and files
    bidder_dirs, all_files = _scan_bidder_directories(b_dir)
    
    # Load additional entries from index files
    index_bidders, index_files = _load_bidders_from_index(b_dir)
    
    # Merge filesystem and index data
    return _merge_bidder_data(bidder_dirs, all_files, index_bidders, index_files)


def _scan_bidder_directories(b_dir: Path) -> tuple[List[str], List[str]]:
    """
    Scan filesystem for bidder directories and files.
    
    This function focuses solely on filesystem scanning, separating
    the concern from index file processing.

    Args:
        b_dir (Path): The B directory to scan

    Returns:
        tuple[List[str], List[str]]: Tuple of (bidder_directories, all_files)
    """
    import unicodedata
    
    # Reserved directory names that should be filtered out
    RESERVED_DIRS = {'md', '.ofs.index.json', 'A', 'B'}
    
    bidder_dirs = []
    all_files = []
    
    try:
        for item in b_dir.iterdir():
            if item.name.startswith('.') or item.name.endswith('.meta.json'):
                continue

            normalized_name = unicodedata.normalize('NFC', item.name)

            if item.is_dir():
                # Filter out reserved directories
                if normalized_name not in RESERVED_DIRS:
                    bidder_dirs.append(normalized_name)
                    # Collect files from within this bidder directory
                    all_files.extend(_collect_files_from_bidder_dir(item))
            elif item.is_file():
                # Files directly in B directory (rare but possible)
                if not normalized_name.startswith('.'):
                    all_files.append(normalized_name)
    except PermissionError:
        pass
    
    return bidder_dirs, all_files


def _collect_files_from_bidder_dir(bidder_dir: Path) -> List[str]:
    """
    Collect files from within a specific bidder directory.
    
    This function handles the nested file collection logic,
    keeping it separate from the main directory scanning.

    Args:
        bidder_dir (Path): The bidder directory to scan for files

    Returns:
        List[str]: List of normalized file names
    """
    import unicodedata
    
    files = []
    try:
        for sub_item in bidder_dir.iterdir():
            if (sub_item.is_file() and
                not sub_item.name.startswith('.') and
                not sub_item.name.endswith('.meta.json')):
                file_name = unicodedata.normalize('NFC', sub_item.name)
                files.append(file_name)
    except PermissionError:
        pass
    
    return files


def _load_bidders_from_index(b_dir: Path) -> tuple[List[str], List[str]]:
    """
    Load bidder information from index files.
    
    This function focuses on extracting bidder and file information
    from index files, separate from filesystem scanning.

    Args:
        b_dir (Path): The B directory containing index files

    Returns:
        tuple[List[str], List[str]]: Tuple of (index_bidders, index_files)
    """
    import unicodedata
    
    # Reserved directory names that should be filtered out
    RESERVED_DIRS = {'md', '.ofs.index.json', 'A', 'B'}
    
    index_bidders = []
    index_files = []
    
    index_data = _load_ofs_index(b_dir)
    if index_data:
        # Add directories from index
        for directory in index_data.get("directories", []):
            dir_name = directory.get("name", "")
            if dir_name:
                normalized_name = unicodedata.normalize('NFC', dir_name)
                if normalized_name not in RESERVED_DIRS:
                    index_bidders.append(normalized_name)

        # Add files from index
        for file_info in index_data.get("files", []):
            file_name = file_info.get("name", "")
            if file_name and not file_name.endswith('.meta.json'):
                normalized_name = unicodedata.normalize('NFC', file_name)
                if not normalized_name.startswith('.'):
                    index_files.append(normalized_name)
    
    return index_bidders, index_files


def _merge_bidder_data(fs_bidders: List[str], fs_files: List[str], 
                      index_bidders: List[str], index_files: List[str]) -> Dict[str, Any]:
    """
    Merge bidder data from filesystem and index sources.
    
    This function handles the final data consolidation and formatting,
    ensuring no duplicates and proper sorting.

    Args:
        fs_bidders (List[str]): Bidders found in filesystem
        fs_files (List[str]): Files found in filesystem
        index_bidders (List[str]): Bidders found in index
        index_files (List[str]): Files found in index

    Returns:
        Dict[str, Any]: Merged and formatted bidder data
    """
    # Merge and deduplicate bidders
    all_bidders = list(set(fs_bidders + index_bidders))
    
    # Merge and deduplicate files
    all_files = list(set(fs_files + index_files))
    
    return {
        "bidder_directories": sorted(all_bidders),
        "all_files": sorted(all_files),
        "total_bidders": len(all_bidders),
        "total_files": len(all_files)
    }


def list_bidder_docs_json(project_name: str, bidder_name: str, include_metadata: bool = False) -> Dict[str, Any]:
    """
    List all documents for a specific bidder in a project in JSON format.
    
    By default, returns a minimal view with document name and basic metadata fields
    (kategorie, meta_name) from .ofs.index.json files when available.
    
    With include_metadata=True, provides full document details including:
    - Complete file information (path, size, type)
    - Full metadata from .ofs.index.json files:
      - Document categorization (kategorie)
      - Document issuer (aussteller)
      - Document name (name)
      - Reasoning for categorization (begründung)
      - Parser information
      - File size and other metadata (excluding hash values)

    Args:
        project_name (str): Name of the project (AUSSCHREIBUNGNAME)
        bidder_name (str): Name of the bidder (BIETERNAME)
        include_metadata (bool): Whether to include full metadata and file details (default: False)

    Returns:
        Dict[str, Any]: JSON structure with documents for the bidder
        - Default: minimal view with name, kategorie, meta_name
        - With metadata: full document details and metadata
    """
    # Define allowed file extensions for documents
    allowed_extensions = {
        # PDF files
        '.pdf',
        # Image files
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.svg', '.webp',
        # Office documents
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp',
        # Text formats
        '.txt', '.md', '.rtf', '.csv', '.json', '.xml'
    }

    # Result structure
    result: Dict[str, Any] = {
        "project": project_name,
        "bidder": bidder_name,
        "documents": [],
        "count": 0
    }

    try:
        base_dir = get_base_dir()
        base_path = Path(base_dir)
        if not base_path.exists():
            return {"error": f"Base directory not found: {base_dir}"}
    except (OSError, PermissionError) as e:
        return {"error": f"Cannot access base directory {base_dir}: {e}"}

    # Find the project directory
    project_path = _search_in_directory(base_path, project_name)
    if not project_path:
        return result

    try:
        project_dir = Path(project_path)
        if not project_dir.exists():
            return {"error": f"Project directory not found: {project_path}"}
    except (OSError, PermissionError) as e:
        return {"error": f"Cannot access project directory {project_path}: {e}"}

    # Find the bidder directory within B/
    b_dir = project_dir / "B" / bidder_name
    if not b_dir.exists():
        # Try case-insensitive search by scanning B directory (for robustness)
        b_dir_parent = project_dir / "B"
        if b_dir_parent.exists():
            for item in b_dir_parent.iterdir():
                if item.is_dir() and item.name.lower() == bidder_name.lower():
                    b_dir = item
                    break

    if not b_dir.exists():
        return result

    # Load metadata from index file if it exists
    index_data = _load_ofs_index(b_dir)
    files_metadata: Dict[str, Any] = {}
    if index_data:
        for file_info in index_data.get("files", []):
            name = file_info.get("name")
            if name:
                files_metadata[name] = file_info

    # Collect documents from filesystem
    try:
        for item in b_dir.iterdir():
            if item.is_file() and not item.name.startswith('.') and not item.name.endswith('.meta.json'):
                ext = item.suffix.lower()
                if ext in allowed_extensions:
                    doc_entry: Dict[str, Any] = {
                        "name": item.name,
                    }

                    # Add metadata overview
                    meta_info = files_metadata.get(item.name, {})
                    meta = meta_info.get("meta", {})
                    if include_metadata:
                        # Include full metadata
                        doc_entry.update({
                            "path": str(item),
                            "size": item.stat().st_size if item.exists() else None,
                            "type": ext,
                            "parsers": meta_info.get("parsers"),
                            "meta": meta,
                        })
                    else:
                        # Include minimal view fields when available
                        doc_entry.update({
                            "kategorie": meta.get("kategorie"),
                            "meta_name": meta.get("name"),
                        })

                    result["documents"].append(doc_entry)
    except PermissionError:
        pass

    # Also include documents listed in index file that might not be in filesystem (rare)
    if index_data:
        for file_info in index_data.get("files", []):
            name = file_info.get("name")
            if name and not any(doc.get("name") == name for doc in result["documents"]):
                # Skip entries that look like sidecar or index files
                if name.startswith('.') or name.endswith('.meta.json'):
                    continue
                ext = Path(name).suffix.lower()
                if ext in allowed_extensions:
                    doc_entry: Dict[str, Any] = {
                        "name": name,
                    }

                    meta = file_info.get("meta", {})
                    if include_metadata:
                        doc_entry.update({
                            "path": str(b_dir / name),
                            "size": None,
                            "type": ext,
                            "parsers": file_info.get("parsers"),
                            "meta": meta,
                        })
                    else:
                        doc_entry.update({
                            "kategorie": meta.get("kategorie"),
                            "meta_name": meta.get("name"),
                        })

                    result["documents"].append(doc_entry)

    result["count"] = len(result["documents"])
    result["total_documents"] = len(result["documents"])
    return result


def list_bidders_json(project_name: str) -> Dict[str, Any]:
    """
    Provide a structured view of bidders and files within the B directory of a project.
    """
    try:
        base_dir = get_base_dir()
        base_path = Path(base_dir)
        if not base_path.exists():
            return {"error": f"Base directory not found: {base_dir}"}
    except (OSError, PermissionError) as e:
        return {"error": f"Cannot access base directory {base_dir}: {e}"}

    # Find the project directory
    project_path = _search_in_directory(base_path, project_name)
    if not project_path:
        return {
            "project": project_name,
            "bidder_directories": [],
            "all_files": [],
            "total_bidders": 0,
            "total_files": 0
        }

    try:
        project_dir = Path(project_path)
        if not project_dir.exists():
            return {"error": f"Project directory not found: {project_path}"}
    except (OSError, PermissionError) as e:
        return {"error": f"Cannot access project directory {project_path}: {e}"}
    b_dir = project_dir / "B"

    return _collect_bidders_structured(b_dir)


def list_project_docs_json(project_name: str, include_metadata: bool = False) -> Dict[str, Any]:
    """
    List all documents in the A directory of a project in JSON format.

    Args:
        project_name (str): Name of the project (AUSSCHREIBUNGNAME)
        include_metadata (bool): Whether to include full metadata and file details

    Returns:
        Dict[str, Any]: JSON structure with documents in the project A directory
    """
    allowed_extensions = {
        '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.svg', '.webp',
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp',
        '.txt', '.md', '.rtf', '.csv', '.json', '.xml'
    }

    result: Dict[str, Any] = {
        "project": project_name,
        "directory": "A",
        "documents": [],
        "count": 0
    }

    try:
        base_dir = get_base_dir()
        base_path = Path(base_dir)
        if not base_path.exists():
            return {"error": f"Base directory not found: {base_dir}"}
    except (OSError, PermissionError) as e:
        return {"error": f"Cannot access base directory {base_dir}: {e}"}

    # Find the project directory
    project_path = _search_in_directory(base_path, project_name)
    if not project_path:
        return result

    try:
        project_dir = Path(project_path)
        if not project_dir.exists():
            return {"error": f"Project directory not found: {project_path}"}
    except (OSError, PermissionError) as e:
        return {"error": f"Cannot access project directory {project_path}: {e}"}

    a_dir = project_dir / "A"
    if not a_dir.exists():
        return result

    # Load metadata from index file if it exists
    index_data = _load_ofs_index(a_dir)
    files_metadata: Dict[str, Any] = {}
    if index_data:
        for file_info in index_data.get("files", []):
            name = file_info.get("name")
            if name:
                files_metadata[name] = file_info

    # Collect documents from filesystem
    try:
        for item in a_dir.iterdir():
            if item.is_file() and not item.name.startswith('.') and not item.name.endswith('.meta.json'):
                ext = item.suffix.lower()
                if ext in allowed_extensions:
                    doc_entry: Dict[str, Any] = {
                        "name": item.name,
                    }

                    meta_info = files_metadata.get(item.name, {})
                    meta = meta_info.get("meta", {})
                    if include_metadata:
                        doc_entry.update({
                            "path": str(item),
                            "size": item.stat().st_size if item.exists() else None,
                            "type": ext,
                            "parsers": meta_info.get("parsers"),
                            "meta": meta,
                        })
                    else:
                        doc_entry.update({
                            "kategorie": meta.get("kategorie"),
                            "meta_name": meta.get("name"),
                        })

                    result["documents"].append(doc_entry)
    except PermissionError:
        pass

    # Include index-only entries if any
    if index_data:
        for file_info in index_data.get("files", []):
            name = file_info.get("name")
            if name and not any(doc.get("name") == name for doc in result["documents"]):
                if name.startswith('.') or name.endswith('.meta.json'):
                    continue
                ext = Path(name).suffix.lower()
                if ext in allowed_extensions:
                    doc_entry: Dict[str, Any] = {
                        "name": name,
                    }

                    meta = file_info.get("meta", {})
                    if include_metadata:
                        doc_entry.update({
                            "path": str(a_dir / name),
                            "size": None,
                            "type": ext,
                            "parsers": file_info.get("parsers"),
                            "meta": meta,
                        })
                    else:
                        doc_entry.update({
                            "kategorie": meta.get("kategorie"),
                            "meta_name": meta.get("name"),
                        })

                    result["documents"].append(doc_entry)

    result["count"] = len(result["documents"])
    result["total_documents"] = len(result["documents"])
    return result


def get_bidder_document_json(project_name: str, bidder_name: str, filename: str, include_metadata: bool = True) -> Dict[str, Any]:
    """
    Get detailed information about a specific bidder document.
    
    Args:
        project_name (str): Name of the project (AUSSCHREIBUNGNAME)
        bidder_name (str): Name of the bidder (BIETERNAME)
        filename (str): Name of the document file
        include_metadata (bool): Whether to include full metadata from .ofs.index.json (default: True)
                                When False, returns minimal view with kategorie and meta_name only

    Returns:
        Dict[str, Any]: Document info including:
        - Basic file information (name, path, size, type)
        - With include_metadata=True: full metadata (parsers, meta, extension, index_size, modified)
        - With include_metadata=False: minimal metadata (kategorie, meta_name)
    """
    try:
        base_dir = get_base_dir()
        base_path = Path(base_dir)
        if not base_path.exists():
            return {"error": f"Base directory not found: {base_dir}"}
    except (OSError, PermissionError) as e:
        return {"error": f"Cannot access base directory {base_dir}: {e}"}

    # Find the project directory
    project_path = _search_in_directory(base_path, project_name)
    if not project_path:
        return {"error": f"Project '{project_name}' not found"}

    try:
        project_dir = Path(project_path)
        if not project_dir.exists():
            return {"error": f"Project directory not found: {project_path}"}
    except (OSError, PermissionError) as e:
        return {"error": f"Cannot access project directory {project_path}: {e}"}
    b_dir = project_dir / "B" / bidder_name

    if not b_dir.exists():
        return {"error": f"Bidder '{bidder_name}' not found in project '{project_name}'"}

    # Path to the file
    file_path = b_dir / filename

    if not file_path.exists():
        return {"error": f"File '{filename}' not found for bidder '{bidder_name}' in project '{project_name}'"}

    # Basic file info
    file_info: Dict[str, Any] = {
        "project": project_name,
        "bidder": bidder_name,
        "name": filename,
        "path": str(file_path),
        "size": file_path.stat().st_size if file_path.exists() else None,
        "type": file_path.suffix.lower(),
    }

    # Add metadata from index file if available
    index_data = _load_ofs_index(b_dir)
    if index_data:
        # Normalize filename for comparison to handle Unicode issues
        normalized_filename = unicodedata.normalize('NFC', filename)
        for entry in index_data.get("files", []):
            entry_name = entry.get("name")
            if entry_name and unicodedata.normalize('NFC', entry_name) == normalized_filename:
                meta = entry.get("meta", {})
                if include_metadata:
                    # Include all available metadata except potential hash fields
                    parsers = entry.get("parsers")
                    extension = entry.get("extension")
                    size = entry.get("size")
                    modified = entry.get("modified")
                    if parsers is not None:
                        file_info["parsers"] = parsers
                    if meta is not None:
                        file_info["meta"] = meta
                    if extension is not None:
                        file_info["extension"] = extension
                    if size is not None:
                        file_info["index_size"] = size
                    if modified is not None:
                        file_info["modified"] = modified
                else:
                    # Include minimal view fields when available
                    file_info["kategorie"] = meta.get("kategorie")
                    file_info["meta_name"] = meta.get("name")
                break

    return file_info


def _select_parser(requested_parser: Optional[str], available_parsers: Dict[str, Any], default_ranking: List[str] = None) -> str:
    """
    Select the best parser based on request, availability, and default ranking.
    
    Args:
        requested_parser: Explicitly requested parser name
        available_parsers: Parser info from .ofs.index.json with structure:
            {"det": ["parser1", "parser2"], "default": "parser1", "status": "..."}
        default_ranking: Preference order for parser selection
    
    Returns:
        Selected parser name
    """
    if default_ranking is None:
        default_ranking = ["docling", "marker", "llamaparse", "pdfplumber"]

    # Extract available parsers from 'det' field or fallback to all non-metadata keys
    available = set()
    default_value = available_parsers.get("default")
    
    # Primary: use 'det' field if available (contains list of detected/available parsers)
    det_parsers = available_parsers.get("det")
    if isinstance(det_parsers, list):
        available = {p.lower() for p in det_parsers if isinstance(p, str)}
    else:
        # Fallback: extract from keys, excluding known metadata fields
        metadata_fields = {"default", "status", "det"}
        for key, value in available_parsers.items():
            if key not in metadata_fields and isinstance(key, str):
                available.add(key.lower())

    # Honor explicit request if available
    if requested_parser:
        rp = requested_parser.lower()
        if rp in available:
            return rp

    # Use default from metadata when valid
    if isinstance(default_value, str) and default_value.lower() in available:
        return default_value.lower()

    # Fall back to ranking
    for candidate in default_ranking:
        if candidate in available:
            return candidate

    # Ultimate fallback
    if available:
        return next(iter(available))
    return "pdfplumber"


def read_doc(identifier: str, parser: Optional[str] = None) -> Dict[str, Any]:
    """
    Read a document content by identifier 'Project@Bidder@Filename'.
    
    This function reads from pre-parsed markdown files in the md/ subfolder,
    following the OFS (Opinionated Filesystem) structure.

    Returns a JSON-like dict with keys: success, error, warning, content, parser, path
    """
    # Validate identifier
    parts = identifier.split('@')
    if len(parts) != 3:
        return {"success": False, "error": "Identifier must be 'Project@Bidder@Filename'"}
    project, bidder, filename = parts

    # Locate project
    try:
        base_dir = get_base_dir()
        base_path = Path(base_dir)
        if not base_path.exists():
            return {"success": False, "error": f"Base directory not found: {base_dir}"}
    except (OSError, PermissionError) as e:
        return {"success": False, "error": f"Cannot access base directory {base_dir}: {e}"}
    
    project_path = _search_in_directory(base_path, project)
    if not project_path:
        return {"success": False, "error": f"Project '{project}' not found"}

    # Determine directory structure: B/bidder for bidder docs, A for tender docs
    try:
        project_dir = Path(project_path)
        if not project_dir.exists():
            return {"success": False, "error": f"Project directory not found: {project_path}"}
    except (OSError, PermissionError) as e:
        return {"success": False, "error": f"Cannot access project directory {project_path}: {e}"}
    if bidder.upper() == "A":
        # Special case: reading from tender documents (A directory)
        doc_dir = project_dir / "A"
        md_dir = doc_dir / "md"
        identifier_context = "tender"
    else:
        # Normal case: reading from bidder documents (B/bidder)
        doc_dir = project_dir / "B" / bidder
        md_dir = doc_dir / "md" 
        identifier_context = "bidder"
    
    if not doc_dir.exists():
        return {"success": False, "error": f"Directory for '{bidder}' not found in project '{project}'"}
    
    if not md_dir.exists():
        return {"success": False, "error": f"Markdown directory (md/) not found for '{bidder}' in project '{project}'"}

    # Check if original file exists (for validation)
    original_file_path = doc_dir / filename
    if not original_file_path.exists():
        return {"success": False, "error": f"Original file '{filename}' not found for {identifier_context} '{bidder}' in project '{project}'"}

    # Load available parsers from index metadata
    md_index = _load_ofs_index(doc_dir)
    available_parsers: Dict[str, Any] = {}
    if md_index:
        # Normalize filename for Unicode comparison (handles composed vs decomposed forms)
        normalized_filename = unicodedata.normalize('NFC', filename)
        for f in md_index.get("files", []):
            file_name = f.get("name")
            if file_name and isinstance(f.get("parsers"), dict):
                normalized_file_name = unicodedata.normalize('NFC', file_name)
                if normalized_file_name == normalized_filename:
                    available_parsers = f["parsers"]
                    break

    selected_parser = _select_parser(parser, available_parsers)

    # Generate possible markdown filenames based on naming conventions
    base_name = Path(filename).stem  # filename without extension
    possible_md_files = [
        f"{base_name}.{selected_parser}.md",      # filename.parser.md
        f"{base_name}_{selected_parser}.md",      # filename_parser.md  
        f"{filename}.{selected_parser}.md",       # filename.ext.parser.md
        f"{filename}_{selected_parser}.md"        # filename.ext_parser.md
    ]
    # Also check subdirectory pattern: md/<base_name>/<base_name>.<parser>.md and underscore variant
    possible_md_subdir_files = [
        str(Path(base_name) / f"{base_name}.{selected_parser}.md"),
        str(Path(base_name) / f"{base_name}_{selected_parser}.md"),
        str(Path(filename) / f"{base_name}.{selected_parser}.md"),  # rare, if folder uses full filename
        str(Path(filename) / f"{base_name}_{selected_parser}.md"),
    ]
    
    # Try to find the markdown file
    md_file_path = None
    actual_parser = selected_parser
    
    for md_filename in possible_md_files:
        candidate_path = md_dir / md_filename
        if candidate_path.exists():
            md_file_path = candidate_path
            break
    if md_file_path is None:
        for md_rel in possible_md_subdir_files:
            candidate_path = md_dir / md_rel
            if candidate_path.exists():
                md_file_path = candidate_path
                break
    
    # If selected parser not found, try fallback to any available parser
    if not md_file_path:
        # Get list of available parsers from directory (root and subfolder)
        all_md_files = list(md_dir.glob(f"{base_name}*.md"))
        all_md_files.extend(md_dir.glob(f"{filename}*.md"))
        all_md_files.extend((md_dir / base_name).glob("*.md") if (md_dir / base_name).exists() else [])
        
        for md_file in all_md_files:
            # Extract parser name from filename
            md_name = md_file.name
            for pattern in [f"{base_name}.", f"{base_name}_", f"{filename}.", f"{filename}_"]:
                if md_name.startswith(pattern) and md_name.endswith(".md"):
                    parser_part = md_name[len(pattern):-3]  # strip prefix and .md
                    if parser_part:  # non-empty
                        found_parser = parser_part
                        md_file_path = md_file
                        actual_parser = found_parser
                        break
            if md_file_path:
                break

    if not md_file_path:
        return {
            "success": False, 
            "error": f"No parsed markdown file found for '{filename}' in md/ directory. Available files: {[f.name for f in md_dir.glob('*.md')][:10]}",
            "path": str(original_file_path)
        }

    # Read the markdown content
    try:
        content = md_file_path.read_text(encoding="utf-8", errors="replace")
        result = {
            "success": True,
            "content": content,
            "parser": actual_parser,
            "path": str(md_file_path),
            "original_path": str(original_file_path)
        }
        
        # Add warning if we had to fall back from requested parser
        if parser and actual_parser != parser:
            result["warning"] = f"Requested parser '{parser}' not found, using '{actual_parser}' instead"
        
        return result
        
    except Exception as e:
        return {
            "success": False, 
            "error": f"Failed to read markdown file: {e}", 
            "path": str(md_file_path)
        }