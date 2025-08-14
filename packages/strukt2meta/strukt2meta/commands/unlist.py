"""
Unlist command handler for processing uncategorized files from a JSON list.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Optional, Union, Dict, Any
from .base import BaseCommand


class UnlistCommand(BaseCommand):
    """Handle the unlist command for processing uncategorized files from a JSON list."""

    def run(self) -> None:
        """Execute the unlist command to process NUM files from un_items.json."""
        # Validate the JSON file exists
        json_file_path = self.validate_file_path(self.args.json_file)

        # Load the JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if 'un_items' not in data:
            self.log("JSON file must contain 'un_items' array", "error")
            return

        # Filter out image files and get uncategorized items
        filtered_items = self._filter_items(data['un_items'])

        if not filtered_items:
            self.log("No suitable files found for processing", "warning")
            return

        # Limit to the requested number
        num_to_process = min(self.args.num, len(filtered_items))
        items_to_process = filtered_items[:num_to_process]

        self.log(
            f"Found {len(filtered_items)} suitable files, processing {num_to_process}")

        if self.args.dry_run:
            self._handle_dry_run(items_to_process)
            return

        # Ask for confirmation unless in quiet mode
        # if not self._get_user_confirmation(num_to_process):
        #    self.log("Processing cancelled", "warning")
        #    return

        # Process the files
        self._process_files(items_to_process, json_file_path)

    def _filter_items(self, un_items: list) -> list:
        """Filter items to exclude image files and include only uncategorized items."""
        image_extensions = {'.png', '.jpg', '.jpeg',
                            '.gif', '.bmp', '.tiff', '.svg', '.webp'}

        filtered = []
        for item in un_items:
            # Skip if not uncategorized
            if not item.get('uncategorized', False):
                continue

            # Skip image files
            path = item.get('path', '')
            file_ext = Path(path).suffix.lower()
            if file_ext in image_extensions:
                if self.verbose:
                    self.log(f"Skipping image file: {path}", "info")
                continue

            filtered.append(item)

        return filtered

    def _handle_dry_run(self, items_to_process: list) -> None:
        """Handle dry run mode for unlist processing."""
        print("🔍 DRY RUN - Files that would be processed:")
        for i, item in enumerate(items_to_process, 1):
            path = item.get('path', 'unknown')
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

    def _process_files(self, items_to_process: list, json_file_path: Path) -> None:
        """Process all selected items."""
        successful = 0
        failed = 0

        for i, item in enumerate(items_to_process, 1):
            path = item.get('path', '')

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

    def _process_single_item(self, item: dict, json_file_path: Path) -> bool:
        """Process a single item from the un_items list."""
        path = item.get('path', '')

        # Check if the file exists in the base directory
        if hasattr(self.args, 'directory') and self.args.directory:
            full_path = Path(self.args.directory) / path
            base_directory = Path(self.args.directory)
        else:
            # Try to find the file relative to the JSON file location
            full_path = json_file_path.parent / path
            base_directory = json_file_path.parent

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
            elif part == 'B':
                if self.verbose:
                    self.log(
                        f"Using 'bdok' prompt for /B/ directory: {file_path}")
                return 'bdok'

        # Fallback to the user-specified prompt or default
        fallback_prompt = self.args.prompt
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
            else:
                # For relative paths, resolve against base_directory
                full_file_path = base_directory / file_path
                file_directory = full_file_path.parent
            
            # Load config for index file name
            index_file_name = '.ofs.index.json'
            try:
                cfg_path = Path('./config.json')
                if cfg_path.exists():
                    with open(cfg_path, 'r', encoding='utf-8') as cfh:
                        cfg = json.load(cfh)
                        index_file_name = cfg.get('index_file_name', index_file_name)
            except Exception:
                pass
            # Determine path (prefer new, fallback to legacy if present)
            index_path = file_directory / index_file_name
            legacy_path = file_directory / '.pdf2md_index.json'
            if not index_path.exists() and legacy_path.exists():
                index_path = legacy_path
            
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
                "backup_enabled": True
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
        status = "ok (json inserted)" if success else "not ok"
        print(f"     {status}")

    def _print_summary(self, successful: int, failed: int, total: int) -> None:
        """Print processing summary."""
        print(f"\n📊 Unlist Processing Complete:")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📁 Total: {total}")

        if successful > 0:
            print(
                f"   📄 Metadata written to index files (.ofs.index.json or legacy .pdf2md_index.json) in each file's directory")

            # Also mention target JSON if specified
            if hasattr(self.args, 'target_json') and self.args.target_json:
                print(
                    f"   📄 Additional metadata written to: {self.args.target_json}")
