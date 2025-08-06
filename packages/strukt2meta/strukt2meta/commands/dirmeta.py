"""
Dirmeta command handler for directory metadata processing.
"""

import json
import os
from pathlib import Path
from .base import BaseCommand


class DirmetaCommand(BaseCommand):
    """Handle the dirmeta command for directory metadata processing."""
    
    def run(self) -> None:
        """Execute the dirmeta command for directory metadata processing."""
        from strukt2meta.file_discovery import FileDiscovery
        from strukt2meta.injector import inject_metadata_to_json

        # Validate directory
        directory_path = self.validate_directory_path(self.args.directory)
        
        if self.verbose:
            self.log(f"Processing directory: {directory_path}", "search")

        # Check for supported files
        if not self._has_supported_files(directory_path):
            self.handle_warning("No supported files found in directory")
            return

        # Discover files with markdown strukts
        discovery = FileDiscovery(str(directory_path))
        mappings = discovery.discover_files()

        if not mappings:
            self.handle_warning("No files with markdown strukts found")
            return

        # Identify files that need metadata processing
        files_to_process = self._identify_files_to_process(mappings, discovery)

        if not files_to_process:
            self.log("No files need metadata processing", "info")
            return

        self.log(f"Found {len(files_to_process)} files needing metadata processing", "info")

        # Process each file
        self._process_files(files_to_process, discovery)
    
    def _has_supported_files(self, directory_path: Path) -> bool:
        """Check if directory contains supported files."""
        supported_extensions = {'.pdf', '.docx', '.txt', '.md'}
        
        for file_path in directory_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                return True
        return False
    
    def _identify_files_to_process(self, mappings, discovery) -> list:
        """Identify files that need metadata processing."""
        files_to_process = []
        
        # Determine JSON file path
        if self.args.json_file:
            json_file_path = self.args.json_file
        else:
            json_file_path = str(Path(self.args.directory) / ".pdf2md_index.json")
        
        for mapping in mappings:
            if not mapping.best_markdown:
                continue
                
            # Check if metadata already exists
            meta_status = discovery.check_metadata_exists(
                mapping.source_file, json_file_path)
            
            # Skip if metadata exists and not overwriting
            if meta_status == "exists" and not self.args.overwrite:
                if self.verbose:
                    self.log(f"Skipping {mapping.source_file} (metadata exists)", "skip")
                continue
                
            files_to_process.append(mapping)
        
        return files_to_process
    
    def _process_files(self, files_to_process, discovery) -> None:
        """Process all files that need metadata."""
        successful = 0
        failed = 0
        
        for i, mapping in enumerate(files_to_process, 1):
            self.log(f"Processing {i}/{len(files_to_process)}: {mapping.source_file}")
            
            try:
                if self._process_single_file(mapping, discovery):
                    successful += 1
                    self.log(f"Processed: {mapping.source_file}", "success")
                else:
                    failed += 1
                    self.handle_warning(f"Processing failed for {mapping.source_file}")
                    
            except Exception as e:
                failed += 1
                self.handle_warning(f"Error processing {mapping.source_file}: {e}")
        
        # Print summary
        self._print_summary(successful, failed, len(files_to_process))
    
    def _process_single_file(self, mapping, discovery) -> bool:
        """Process a single file for metadata extraction."""
        try:
            # Read the markdown file
            md_path = discovery.md_directory / mapping.best_markdown
            with open(md_path, "r", encoding="utf-8") as f:
                input_text = f.read()
            
            # Load prompt and analyze
            prompt = self.load_prompt(self.args.prompt)
            json_cleanup = getattr(self.args, 'json_cleanup', False)
            result = self.query_ai_model(prompt, input_text, verbose=self.verbose, json_cleanup=json_cleanup)
            
            # Extract metadata from result
            metadata = self._extract_metadata_from_result(result, mapping.source_file)
            
            if not metadata:
                self.log(f"No metadata extracted for {mapping.source_file}", "warning")
                return False
            
            # Inject metadata into JSON index
            return self._inject_metadata(metadata, mapping.source_file)
            
        except Exception as e:
            self.log(f"Error processing {mapping.source_file}: {e}", "error")
            return False
    
    def _extract_metadata_from_result(self, result, source_file: str) -> dict:
        """Extract metadata from AI model result."""
        try:
            # Handle different result types
            if isinstance(result, dict):
                return result
            elif isinstance(result, str):
                # Try to parse as JSON
                try:
                    parsed = json.loads(result)
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    pass
                
                # Handle truncated documents
                if "document appears to be truncated" in result.lower():
                    self.log(f"Document truncated for {source_file}, retrying with shorter prompt", 
                            "warning")
                    # Could implement retry logic here
                    return {}
                
                # Fallback: wrap string result
                return {"extracted_content": result}
            else:
                return {"extracted_content": str(result)}
                
        except Exception as e:
            self.log(f"Error extracting metadata from result: {e}", "error")
            return {}
    
    def _inject_metadata(self, metadata: dict, source_file: str) -> bool:
        """Inject metadata into JSON index."""
        from strukt2meta.injector import inject_metadata_to_json
        
        try:
            # Determine JSON file path
            if self.args.json_file:
                json_path = Path(self.args.json_file)
            else:
                json_path = Path(self.args.directory) / ".pdf2md_index.json"
            
            # Inject metadata using correct parameter names
            success = inject_metadata_to_json(
                source_filename=source_file,
                metadata=metadata,
                json_file_path=str(json_path),
                base_directory=self.args.directory
            )
            
            return success
            
        except Exception as e:
            self.log(f"Error injecting metadata for {source_file}: {e}", "error")
            return False
    
    def _print_summary(self, successful: int, failed: int, total: int) -> None:
        """Print processing summary."""
        print(f"\n📊 Directory Metadata Processing Complete:")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📁 Total: {total}")
        
        if successful > 0:
            # Determine JSON file path for display
            if self.args.json_file:
                json_file_display = self.args.json_file
            else:
                json_file_display = str(Path(self.args.directory) / ".pdf2md_index.json")
            print(f"   📄 Metadata written to: {json_file_display}")