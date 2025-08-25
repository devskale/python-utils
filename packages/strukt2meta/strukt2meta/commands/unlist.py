"""
Unlist command handler for processing uncategorized files.

Two modes are supported:
1) Legacy JSON mode (if --json-file is provided or <directory>/un_items.json exists):
    Reads a JSON list of files and processes them.
2) OFS mode (default):
    Uses the OFS package to:
      - list projects
      - list bidders per project
      - list documents (A and B scope) including metadata
      - identify uncategorized or missing-metadata documents
    Then processes those documents end-to-end.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Optional, Union, Dict, Any, List
from .base import BaseCommand


class UnlistCommand(BaseCommand):
    """Handle the unlist command for processing uncategorized files from a JSON list."""

    def run(self) -> None:
        """Execute the unlist command.

        If a JSON list is specified (legacy), use it; otherwise, use OFS to
        auto-discover uncategorized or missing-metadata documents and process them.
        """
        # Legacy JSON mode if explicitly requested/provided
        legacy_json = getattr(self.args, 'json_file', None)
        if legacy_json:
            return self._run_legacy_json_mode()

        # Else: OFS-backed traversal is the default
        return self._run_ofs_mode()

    # -----------------------------
    # Legacy JSON mode (back-compat)
    # -----------------------------
    def _run_legacy_json_mode(self) -> None:
        # Resolve and validate base directory
        dir_arg = getattr(self.args, 'directory', None)
        if isinstance(dir_arg, str) and dir_arg:
            base_dir = self.validate_directory_path(dir_arg)
        else:
            # Infer base_dir from json_file if absolute; otherwise current working dir
            jf_path = Path(self.args.json_file)
            base_dir = jf_path.parent if jf_path.is_absolute() else Path.cwd()

        # Determine JSON file path (explicit)
        jf = Path(self.args.json_file)
        json_file_path = jf if jf.is_absolute() else (base_dir / jf)
        if not json_file_path.exists():
            self.log(f"JSON file not found: {self.args.json_file}", "error")
            return

        # Ensure downstream helpers see the directory base as well
        setattr(self.args, 'directory', str(base_dir))

        # Load the JSON file
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.log(f"Failed to read JSON file {json_file_path}: {e}", "error")
            return

        # Accept both legacy key 'un_items' and new key 'files'
        if 'un_items' in data:
            raw_items = data['un_items']
        elif 'files' in data:
            raw_items = data['files']
        else:
            self.log("No 'un_items' found in JSON file", "error")
            return

        filtered_items = self._filter_items(raw_items)
        if not filtered_items:
            self.log("No suitable files found for processing", "warning")
            return

        # Limit and process
        num_arg = getattr(self.args, 'num', None)
        num_to_process = len(filtered_items) if (num_arg is None or num_arg <= 0) else min(num_arg, len(filtered_items))
        items_to_process = filtered_items[:num_to_process]

        self.log(f"Found {len(filtered_items)} suitable files, processing {num_to_process}")
        if self.args.dry_run:
            self._handle_dry_run(items_to_process)
            return
        self._process_files(items_to_process, json_file_path)

    # -----------------------------
    # OFS mode (default)
    # -----------------------------
    def _run_ofs_mode(self) -> None:
        """Traverse the OFS structure to find uncategorized/missing-metadata docs and process them."""
        try:
            from ofs.api import list_projects, list_bidders_for_project, docs_list
            # Allow overriding OFS BASE_DIR from positional 'directory'
            base_override = getattr(self.args, 'directory', None)
            if isinstance(base_override, str) and base_override.strip():
                base_path = Path(base_override).resolve()
                if base_path.exists():
                    # Set env for any downstream consumers
                    os.environ['OFS_BASE_DIR'] = str(base_path)
                    # Update live OFS config singleton
                    try:
                        from ofs.config import get_config
                        get_config().set('BASE_DIR', str(base_path))
                    except Exception:
                        pass
        except Exception as e:
            self.log(f"OFS package not available or failed to import: {e}", "error")
            return

        # Gather uncategorized docs across all projects (A and B scopes)
        items: List[Dict[str, Any]] = []

        # Projects
        projects_json = list_projects()
        projects: List[str] = []
        if isinstance(projects_json, dict):
            projects = projects_json.get('projects') or []
        elif isinstance(projects_json, list):
            projects = projects_json
        # Fallback: if still empty, scan the provided base directory for projects (dirs only)
        if not projects:
            base_override = os.environ.get('OFS_BASE_DIR')
            if base_override:
                try:
                    p = Path(base_override)
                    if p.exists():
                        projects = [d.name for d in p.iterdir() if d.is_dir() and not d.name.startswith('.') and d.name not in {'md','archive'}]
                except Exception:
                    pass

        if not projects:
            self.log("No OFS projects found.", "warning")
            return

        for project in projects:
            # A/ documents with metadata view
            try:
                a_docs = docs_list(project, meta=True)
                items.extend(self._gather_uncategorized_from_docs(a_docs, scope='A', project=project))
            except Exception as e:
                if self.verbose:
                    self.log(f"Docs listing for A in project '{project}' failed: {e}", "warning")

            # B/ bidders and their documents
            try:
                bidders = list_bidders_for_project(project)
            except Exception as e:
                bidders = []
                if self.verbose:
                    self.log(f"Listing bidders for project '{project}' failed: {e}", "warning")

            for bidder in bidders or []:
                try:
                    b_docs = docs_list(f"{project}@{bidder}", meta=True)
                    items.extend(self._gather_uncategorized_from_docs(b_docs, scope='B', project=project, bidder=bidder))
                except Exception as e:
                    if self.verbose:
                        self.log(f"Docs listing for B '{bidder}' in project '{project}' failed: {e}", "warning")

        if not items:
            self.log("No uncategorized or missing-metadata documents found in OFS.", "success")
            return

        # Apply --num limit if provided
        num_arg = getattr(self.args, 'num', None)
        num_to_process = len(items) if (num_arg is None or num_arg <= 0) else min(num_arg, len(items))
        items_to_process = items[:num_to_process]

        self.log(f"Found {len(items)} uncategorized/missing-metadata docs, processing {num_to_process}")

        if self.args.dry_run:
            self._handle_dry_run(items_to_process)
            return

        # Prevent legacy path prefixing with positional 'directory' in OFS mode
        try:
            setattr(self.args, 'directory', '')
        except Exception:
            pass

        # In OFS mode, we don't have a json_file context; pass None
        self._process_files(items_to_process, None)

    def _filter_items(self, un_items: list) -> list:
        """Filter items to exclude image files and include only uncategorized items when status is present.

        Logic:
        - If item has key 'category', include only when category == 'uncategorized'
        - Else if item has key 'uncategorized' (bool), include only when True
        - Else (no explicit status), include by default
        - In all cases, skip common image extensions
        """
        image_extensions = {'.png', '.jpg', '.jpeg',
                            '.gif', '.bmp', '.tiff', '.svg', '.webp'}

        filtered = []
        for item in un_items:
            # Skip image files
            path = item.get('path') or item.get('file_path') or item.get('file', '')
            file_ext = Path(path).suffix.lower()
            if file_ext in image_extensions:
                if self.verbose:
                    self.log(f"Skipping image file: {path}", "info")
                continue

            # Determine uncategorized status
            include = True
            if 'category' in item:
                include = (str(item.get('category', '')).lower() == 'uncategorized')
            elif 'uncategorized' in item:
                include = bool(item.get('uncategorized'))

            if include:
                filtered.append(item)

        return filtered

    def _handle_dry_run(self, items_to_process: list) -> None:
        """Handle dry run mode for unlist processing."""
        print("🔍 DRY RUN - Files that would be processed:")
        for i, item in enumerate(items_to_process, 1):
            path = item.get('path') or item.get('file_path') or item.get('file', 'unknown')
            unparsed = item.get('unparsed', False)
            prompt_name = self._determine_prompt_for_path(path)
            print(f"   {i}. 📄 {path}")
            print(f"      🎯 Prompt: {prompt_name}")
            if unparsed:
                print(f"      ⚠️  File is marked as unparsed")

    def _get_user_confirmation(self, count: int) -> bool:
        """Get user confirmation for processing."""
        print(f"\n🚀 Process {count} files for categorization? (y/N): ", end="")
        return input().strip().lower() == 'y'

    def _process_files(self, items_to_process: list, json_file_path: Optional[Path]) -> None:
        """Process all selected items."""
        successful = 0
        failed = 0

        for i, item in enumerate(items_to_process, 1):
            path = item.get('path') or item.get('file_path') or item.get('file', '')

            try:
                if self._process_single_item(item, json_file_path):
                    successful += 1
                else:
                    failed += 1

            except Exception as e:
                if self.verbose:
                    self.handle_warning(f"Error processing {path}: {str(e)}")
                failed += 1

        # Summary
        self._print_summary(successful, failed, len(items_to_process))

    def _process_single_item(self, item: dict, json_file_path: Optional[Path]) -> bool:
        """Process a single item from the un_items list."""
        path = item.get('path') or item.get('file_path') or item.get('file', '')

        # Check if the file exists in the base directory
        p = Path(path)
        if p.is_absolute():
            full_path = p
            base_directory = p.parent
        elif hasattr(self.args, 'directory') and self.args.directory:
            full_path = Path(self.args.directory) / path
            base_directory = full_path.parent
        else:
            # Try to find the file relative to the JSON file location
            if json_file_path is not None:
                full_path = json_file_path.parent / path
                base_directory = full_path.parent
            else:
                full_path = Path.cwd() / path
                base_directory = full_path.parent

        if not full_path.exists():
            self.log(f"File not found: {full_path}", "warning")
            self._print_categorization_result(path, None, "unknown", None, None, False)
            return False

        # Determine the appropriate prompt based on file structure
        prompt_name = self._determine_prompt_for_path(path)
        
        # Try to use file discovery to find the best markdown file
        chosen_md_file = None
        parser_used = None
        content = None
        
        try:
            from strukt2meta.file_discovery import FileDiscovery
            # Use the file's directory for discovery, not the base directory
            file_directory = full_path.parent
            discovery = FileDiscovery(str(file_directory))
            chosen_md_file = discovery.get_best_markdown_for_file(full_path.name)
            
            if chosen_md_file:
                # Use the discovered markdown file
                md_path = Path(chosen_md_file)
                if md_path.exists():
                    # Extract parser name from the chosen markdown file
                    md_stem = md_path.stem
                    # Try dot-separated format first
                    dot_parts = md_stem.split('.')
                    if len(dot_parts) >= 2:
                        parser_used = dot_parts[-1]  # Last part before .md
                    else:
                        # Try underscore-separated format
                        underscore_parts = md_stem.split('_')
                        if len(underscore_parts) >= 2:
                            parser_used = underscore_parts[-1]  # Last part before .md
                        else:
                            # This is a direct markdown file (no parser suffix)
                            parser_used = "direct"
                    
                    with open(md_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
        except Exception as e:
            if self.verbose:
                self.log(f"File discovery failed for {path}: {str(e)}", "warning")
        
        # Fallback to direct content extraction if no markdown file found
        if not content:
            content = self._extract_content(full_path)
            chosen_md_file = None
            # Determine parser type for direct extraction
            parser_used = self._get_direct_parser_type(full_path)
            
        if not content:
            self.log(f"Could not extract content from: {path}", "warning")
            self._print_categorization_result(path, None, prompt_name, chosen_md_file, parser_used, False)
            return False

        # Generate metadata using AI
        try:
            prompt = self.load_prompt(prompt_name)
            result = self.query_ai_model(
                prompt,
                content,
                verbose=self.verbose,
                json_cleanup=getattr(self.args, 'json_cleanup', False)
            )

            # Always update the index file with the generated metadata
            success = self._update_index_file(result, path, base_directory, prompt_name, parser_used)

            # If we have a target JSON file for injection, also inject there
            if hasattr(self.args, 'target_json') and self.args.target_json:
                target_success = self._inject_metadata(
                    result, path, self.args.target_json)
                success = success and target_success

            # Print simplified result
            self._print_categorization_result(path, result, prompt_name, chosen_md_file, parser_used, success)
            return success

        except Exception as e:
            self.log(f"AI processing failed for {path}: {str(e)}", "warning")
            self._print_categorization_result(path, None, prompt_name, chosen_md_file, parser_used, False)
            return False

    # -----------------------------
    # OFS helpers
    # -----------------------------
    def _gather_uncategorized_from_docs(self, docs_json: Dict[str, Any], scope: str, project: str, bidder: Optional[str] = None) -> List[Dict[str, Any]]:
        """Produce a list of items (dicts) with 'path' for documents considered uncategorized/missing-metadata.

        The returned items are compatible with the existing processing pipeline.
        """
        results: List[Dict[str, Any]] = []
        if not isinstance(docs_json, dict):
            return results

        documents = docs_json.get('documents') or []
        for d in documents:
            # Skip images and JSON (e.g., audit.json) similar to legacy filtering
            image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.svg', '.webp'}
            ext = None
            if isinstance(d.get('type'), str):
                ext = d['type'].lower()
            elif isinstance(d.get('name'), str):
                ext = Path(d['name']).suffix.lower()
            elif isinstance(d.get('path'), str):
                ext = Path(d['path']).suffix.lower()
            if ext in image_extensions or ext == '.json':
                continue

            # Prefer 'path' when include_metadata=True, otherwise compose minimal path from known fields
            path = d.get('path')
            if not path:
                name = d.get('name') or d.get('filename')
                if not name:
                    continue
                # Compose best-effort path using scope
                try:
                    from ofs.paths import get_path as ofs_get_path
                    project_dir = Path(ofs_get_path(project))
                    if scope == 'A':
                        composed = project_dir / 'A' / name
                    else:
                        composed = project_dir / 'B' / (bidder or '') / name
                    path = str(composed)
                except Exception:
                    path = name  # fallback relative

            if self._is_uncategorized(d):
                results.append({
                    'path': path,
                    'project': project,
                    **({'bidder': bidder} if bidder else {})
                })
        return results

    def _is_uncategorized(self, doc_entry: Dict[str, Any]) -> bool:
        """Determine if a document is uncategorized or missing metadata.

        Heuristics:
        - No 'meta' dict present
        - 'meta' present but missing 'kategorie' or 'name'
        - 'kategorie' equals 'uncategorized' (case-insensitive)
        """
        meta = doc_entry.get('meta')
        if not isinstance(meta, dict) or not meta:
            return True
        kategorie = meta.get('kategorie')
        name = meta.get('name')
        if kategorie is None or name is None:
            return True
        if isinstance(kategorie, str) and kategorie.strip().lower() == 'uncategorized':
            return True
        return False

    def _determine_prompt_for_path(self, file_path: str) -> str:
        """
        Determine the appropriate prompt based on the opinionated file structure.

        Args:
            file_path: The file path to analyze

        Returns:
            The prompt name to use based on the directory structure
        """
        # Convert to Path for easier manipulation
        path_parts = Path(file_path).parts

        # Check for opinionated directory structure
        for part in path_parts:
            if part == 'A':
                if self.verbose:
                    self.log(
                        f"Using 'adok' prompt for /A/ directory: {file_path}")
                return 'adok'
            if part == 'B':
                if self.verbose:
                    self.log(
                        f"Using 'bdok' prompt for /B/ directory: {file_path}")
                return 'bdok'

        # Fallback to the user-specified prompt or default
        fallback_prompt = getattr(self.args, 'prompt', None)
        if not isinstance(fallback_prompt, str) or not fallback_prompt:
            fallback_prompt = 'metadata_extraction'
        if self.verbose:
            self.log(
                f"Using fallback prompt '{fallback_prompt}' for: {file_path}")
        return fallback_prompt

    def _extract_content(self, file_path: Path) -> str:
        """Extract text content from various file types."""
        try:
            # For now, handle text-based files
            text_extensions = {'.txt', '.md', '.csv', '.json', '.xml', '.html'}

            if file_path.suffix.lower() in text_extensions:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()

            # For other files, try to extract filename and basic info
            return f"Filename: {file_path.name}\nPath: {file_path}\nSize: {file_path.stat().st_size} bytes"

        except Exception as e:
            self.log(f"Error reading file {file_path}: {str(e)}", "warning")
            return ""

    def _get_direct_parser_type(self, file_path: Path) -> str:
        """Determine the parser type used for direct content extraction."""
        file_extension = file_path.suffix.lower()
        
        # Map file extensions to likely parser types
        if file_extension == '.pdf':
            return 'docling'  # Default PDF parser
        elif file_extension in {'.txt', '.md'}:
            return 'text'
        elif file_extension in {'.csv', '.json', '.xml', '.html'}:
            return 'text'
        elif file_extension == '.docx':
            return 'docling'  # Default DOCX parser
        elif file_extension == '.xlsx':
            return 'docling'  # Default XLSX parser
        else:
            return 'basic'  # Basic file info extraction

    def _update_index_file(self, result: Union[Dict[str, Any], str], file_path: str, base_directory: Path, prompt_name: str, parser_used: Optional[str] = None) -> bool:
        """Update the configured index JSON file in the file's directory with metadata.

        Supports new default '.ofs.index.json' and falls back to legacy '.pdf2md_index.json' if that exists.
        """
        try:
            import json
            from datetime import datetime
            from strukt2meta.injector import inject_metadata_to_json
            from strukt2meta.jsonclean import cleanify_json
            
            # Determine the file's directory
            file_path_obj = Path(file_path)
            if file_path_obj.is_absolute():
                file_directory = file_path_obj.parent
                full_file_path = file_path_obj
            else:
                # For relative paths, treat base_directory as the actual file directory
                # and avoid re-attaching subfolders that are already included in file_path
                file_directory = base_directory
                full_file_path = base_directory / file_path_obj.name
            
            # Use only the modern OFS index file name
            index_file_name = '.ofs.index.json'
            index_path = file_directory / index_file_name
            
            # Clean and extract metadata from the AI result
            if isinstance(result, dict):
                metadata = result
            else:
                # Clean the AI output using cleanify_json
                try:
                    cleaned_result = cleanify_json(str(result))
                    if isinstance(cleaned_result, dict):
                        metadata = cleaned_result
                    else:
                        # If cleanify_json doesn't return a dict, wrap it
                        metadata = {"extracted_content": cleaned_result}
                except Exception as clean_error:
                    if self.verbose:
                        self.log(f"JSON cleanup failed for {file_path}: {str(clean_error)}, using raw result", "warning")
                    # Fallback: wrap the raw result
                    metadata = {"extracted_content": str(result)}
            
            # Add AI generation information
            try:
                # Load config to get provider and model information
                config_path = Path("./config.json")
                if config_path.exists():
                    with open(config_path, "r") as config_file:
                        config = json.load(config_file)
                    provider_name = config.get("provider", "unknown")
                    model_name = config.get("model", "unknown")
                else:
                    provider_name = "unknown"
                    model_name = "unknown"
                
                # Generate current date in ISO format
                current_date = datetime.now().strftime("%Y-%m-%d")
                
                # Add Autor field to indicate AI generation with prompt and parser information
                if parser_used:
                    metadata["Autor"] = f"KI-generiert {provider_name}@{model_name}@{prompt_name}@{parser_used} {current_date}"
                else:
                    metadata["Autor"] = f"KI-generiert {provider_name}@{model_name}@{prompt_name} {current_date}"
                
            except Exception as autor_error:
                if self.verbose:
                    self.log(f"Failed to add Autor field for {file_path}: {str(autor_error)}", "warning")
                # Add fallback Autor field
                if parser_used:
                    metadata["Autor"] = f"KI-generiert unknown@unknown@{prompt_name}@{parser_used} {datetime.now().strftime('%Y-%m-%d')}"
                else:
                    metadata["Autor"] = f"KI-generiert unknown@unknown@{prompt_name} {datetime.now().strftime('%Y-%m-%d')}"
            
            # Inject metadata into the index file
            success = inject_metadata_to_json(
                source_filename=file_path_obj.name,  # Use just the filename for the index
                metadata=metadata,
                json_file_path=str(index_path),
                base_directory=str(file_directory)
            )
            
            if success and self.verbose:
                self.log(f"Updated {index_path} with metadata for: {file_path}", "success")
            
            return success
            
        except Exception as e:
            self.log(f"Error updating index file for {file_path}: {str(e)}", "warning")
            return False

    def _inject_metadata(self, result: Union[Dict[str, Any], str], file_path: str, target_json: str) -> bool:
        """Inject generated metadata into target JSON file."""
        try:
            # Create injection parameters
            params = {
                "input_data": result,
                "json_inject_file": target_json,
                "target_filename": file_path,
                "injection_schema": {
                    "meta": {
                        "kategorie": {"ai_generated_field": True},
                        "name": {"ai_generated_field": True},
                        "dokumenttyp": {"ai_generated_field": True},
                        "thema": {"ai_generated_field": True},
                        "sprache": {"ai_generated_field": True}
                    }
                },
                "backup_enabled": False
            }

            # Create temporary parameter file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(params, f, indent=2, ensure_ascii=False)
                temp_param_file = f.name

            try:
                # Process with injector
                from strukt2meta.injector import JSONInjector
                injector = JSONInjector(temp_param_file)
                injection_result = injector.inject()
                return injection_result.get('success', False)

            finally:
                # Clean up temp file
                os.unlink(temp_param_file)

        except Exception as e:
            self.log(f"Injection failed: {str(e)}", "warning")
            return False

    def _print_categorization_result(self, file_path: str, result, prompt_name: str, chosen_md_file: Optional[str] = None, parser_used: Optional[str] = None, success: bool = True) -> None:
        """Print simplified categorization result for a file."""
        # Show source file
        print(f"📄 {file_path} (sourcefile)")
        
        # Show prompt and parser type
        if chosen_md_file and parser_used:
            print(f"     {prompt_name} @ ({parser_used})")
        elif parser_used:
            print(f"     {prompt_name} @ ({parser_used})")
        else:
            print(f"     {prompt_name} @ (content extracted directly)")
        
        # Show success status
        if success:
            # Try to surface key fields in the success message
            name = None
            kategorie = None

            # 1) Try to extract from result directly (dict or JSON string)
            try:
                payload = result
                if isinstance(payload, str):
                    try:
                        payload = json.loads(payload)
                    except Exception:
                        # Try robust cleanup for loosely-structured JSON
                        try:
                            from strukt2meta.jsonclean import cleanify_json
                            payload = cleanify_json(payload)
                        except Exception:
                            payload = None
                if isinstance(payload, dict):
                    # Look for direct keys first
                    name = payload.get("name")
                    kategorie = payload.get("kategorie")
                    # Or nested under meta
                    if (name is None or kategorie is None) and isinstance(payload.get("meta"), dict):
                        meta = payload.get("meta", {})
                        name = name or meta.get("name")
                        kategorie = kategorie or meta.get("kategorie")
            except Exception:
                name = None
                kategorie = None

            # 2) If still missing, try reading the index file written for this item
            if not (name or kategorie):
                try:
                    file_path_obj = Path(file_path)
                    # Determine directory similar to _update_index_file
                    if file_path_obj.is_absolute():
                        file_directory = file_path_obj.parent
                        fname = file_path_obj.name
                    else:
                        base_dir = getattr(self.args, 'directory', None)
                        if base_dir:
                            file_directory = Path(base_dir) / file_path_obj
                            file_directory = file_directory.parent
                            fname = file_path_obj.name
                        else:
                            file_directory = Path.cwd()
                            fname = file_path_obj.name

                    # Resolve index filename (fixed)
                    index_file_name = '.ofs.index.json'
                    index_path = file_directory / index_file_name

                    if index_path.exists():
                        with open(index_path, 'r', encoding='utf-8') as ifh:
                            idx = json.load(ifh)
                        files = idx.get('files') if isinstance(idx, dict) else None
                        if isinstance(files, list):
                            for entry in files:
                                if isinstance(entry, dict) and entry.get('name') == fname:
                                    meta = entry.get('meta') or {}
                                    if isinstance(meta, dict):
                                        name = name or meta.get('name')
                                        kategorie = kategorie or meta.get('kategorie')
                                    break
                except Exception:
                    # Silently ignore and fallback
                    pass

            # Finalize message
            if name or kategorie:
                parts = []
                parts.append(str(name) if name is not None else "")
                parts.append(str(kategorie) if kategorie is not None else "")
                descriptor = ", ".join(p for p in parts if p)
                print(f"     ok ({descriptor})")
            else:
                print("     ok (json inserted)")
        else:
            print("     not ok")

    def _print_summary(self, successful: int, failed: int, total: int) -> None:
        """Print processing summary."""
        print(f"\n📊 Unlist Processing Complete:")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📁 Total: {total}")

        if successful > 0:
            print(
                f"   📄 Metadata written to .ofs.index.json in each file's directory")

            # Also mention target JSON if specified
            if hasattr(self.args, 'target_json') and self.args.target_json:
                print(
                    f"   📄 Additional metadata written to: {self.args.target_json}")
