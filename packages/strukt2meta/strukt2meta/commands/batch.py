"""
Batch command handler for intelligent batch processing of multiple files.
"""

import json
import os
import tempfile
from .base import BaseCommand


class BatchCommand(BaseCommand):
    """Handle the batch command for intelligent batch processing."""

    def run(self) -> None:
        """Execute the batch command for processing multiple files."""
        from strukt2meta.file_discovery import FileDiscovery
        from strukt2meta.injector import JSONInjector

        # Validate directory
        directory_path = self.validate_directory_path(self.args.directory)

        discovery = FileDiscovery(str(directory_path), self.args.config)
        mappings = discovery.discover_files()

        if not mappings:
            self.log("No files found for processing", "error")
            return

        # Filter mappings to only include those with good markdown files
        valid_mappings = self._filter_valid_mappings(mappings)

        if self.verbose:
            self.log(f"Found {len(mappings)} total files")
            self.log(
                f"{len(valid_mappings)} files have suitable markdown", "success")

        if self.args.dry_run:
            self._handle_dry_run(valid_mappings)
            return

        # Ask for confirmation
#        if not self._get_user_confirmation(len(valid_mappings)):
#            self.log("Batch processing cancelled", "warning")
#            return

        # Process files
        self._process_files(valid_mappings, discovery)

    def _filter_valid_mappings(self, mappings) -> list:
        """Filter mappings to include only those with good markdown files."""
        return [m for m in mappings
                if m.best_markdown and m.confidence_score > 0.3]

    def _handle_dry_run(self, valid_mappings) -> None:
        """Handle dry run mode for batch processing."""
        print("🔍 DRY RUN - Files that would be processed:")
        for mapping in valid_mappings:
            print(f"   📄 {mapping.source_file}")
            print(f"      → {mapping.best_markdown} ({mapping.parser_used})")

    def _get_user_confirmation(self, count: int) -> bool:
        """Get user confirmation for batch processing."""
        print(f"\n🚀 Process {count} files? (y/N): ", end="")
        return input().strip().lower() == 'y'

    def _process_files(self, valid_mappings, discovery) -> None:
        """Process all valid file mappings."""
        successful = 0
        failed = 0

        for i, mapping in enumerate(valid_mappings, 1):
            self.log(
                f"Processing {i}/{len(valid_mappings)}: {mapping.source_file}")

            # Show which markdown file and parser will be used (verbose mode)
            if self.verbose:
                details = []
                if getattr(mapping, 'best_markdown', None):
                    details.append(str(mapping.best_markdown))
                if getattr(mapping, 'parser_used', None):
                    details.append(f"parser={mapping.parser_used}")
                if details:
                    self.log("Using " + " | ".join(details), "info")

            try:
                if self._process_single_file(mapping, discovery):
                    if self.verbose and getattr(mapping, 'parser_used', None):
                        self.log(
                            f"Success: {mapping.source_file} [{mapping.parser_used}]", "success")
                    else:
                        self.log(f"Success: {mapping.source_file}", "success")
                    successful += 1
                else:
                    self.handle_warning(
                        f"Processing failed for {mapping.source_file}")
                    failed += 1

            except Exception as e:
                self.handle_warning(
                    f"Error processing {mapping.source_file}: {str(e)}")
                failed += 1

        # Summary
        self._print_summary(successful, failed, len(valid_mappings))

    def _process_single_file(self, mapping, discovery) -> bool:
        """Process a single file mapping."""
        # Create temporary parameter file
        md_path = str(discovery.md_directory / mapping.best_markdown)

        params = {
            "input_path": md_path,
            "prompt": self.args.prompt,
            "json_inject_file": self.args.json_file,
            "target_filename": mapping.source_file,
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
            result = injector.inject()
            return result['success']

        finally:
            # Clean up temp file
            os.unlink(temp_param_file)

    def _print_summary(self, successful: int, failed: int, total: int) -> None:
        """Print batch processing summary."""
        print(f"\n📊 Batch Processing Complete:")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📁 Total: {total}")
