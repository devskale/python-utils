"""
Clearmeta command handler for clearing metadata fields from JSON files.
"""

import json
import os
from pathlib import Path
from .base import BaseCommand


class ClearmetaCommand(BaseCommand):
    """Handle the clearmeta command for clearing metadata fields."""
    
    def run(self) -> None:
        """Execute the clearmeta command to clear metadata fields from JSON file."""
        # Validate JSON file
        json_path = self.validate_file_path(self.args.json_file)
        
        if self.verbose:
            self.log(f"Processing JSON file: {json_path}", "search")

        # Load JSON data
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.handle_error(e, f"Invalid JSON in file {json_path}")
        except Exception as e:
            self.handle_error(e, f"Reading file {json_path}")

        # Parse fields to clear
        fields_to_clear = self._parse_fields_to_clear()
        
        if not fields_to_clear:
            self.log("No fields specified to clear", "warning")
            return

        # Clear metadata fields
        cleared_count = self._clear_metadata_fields(data, fields_to_clear)
        
        if cleared_count == 0:
            self.log("No metadata fields were cleared", "info")
            return

        # Write back to file (no backup to prevent .bak files)
        if not self.args.dry_run:
            self._write_json_file(json_path, data)
            self.log(f"Cleared {cleared_count} metadata field occurrences", "success")
        else:
            self.log(f"DRY RUN: Would clear {cleared_count} metadata field occurrences", "info")

        # Print summary
        self._print_summary(cleared_count, fields_to_clear, json_path)
    
    def _parse_fields_to_clear(self) -> list:
        """Parse the fields to clear from command arguments."""
        if hasattr(self.args, 'fields') and self.args.fields:
            # Split by comma and strip whitespace
            fields = [field.strip() for field in self.args.fields.split(',')]
            return [field for field in fields if field]  # Remove empty strings
        elif hasattr(self.args, 'all') and self.args.all:
            return ['ALL']  # Special marker for clearing all metadata
        else:
            return []
    
    def _clear_metadata_fields(self, data: dict, fields_to_clear: list) -> int:
        """
        Clear specified metadata fields from all files in the JSON data.
        
        Args:
            data: JSON data structure
            fields_to_clear: List of field names to clear, or ['ALL'] for all fields
            
        Returns:
            Number of field occurrences cleared
        """
        cleared_count = 0
        
        if 'files' not in data:
            self.log("No 'files' section found in JSON", "warning")
            return 0
        
        for file_entry in data['files']:
            if 'meta' not in file_entry:
                continue
                
            meta = file_entry['meta']
            original_field_count = len(meta)
            
            if 'ALL' in fields_to_clear:
                # Clear all metadata fields
                cleared_count += len(meta)
                file_entry['meta'] = {}
                if self.verbose:
                    self.log(f"Cleared all {original_field_count} metadata fields from {file_entry.get('name', 'unknown')}")
            else:
                # Clear specific fields (case-insensitive matching)
                fields_cleared_for_file = 0
                fields_to_remove = []
                
                # Find all matching fields (case-insensitive)
                for field_to_clear in fields_to_clear:
                    field_lower = field_to_clear.lower()
                    for existing_field in meta.keys():
                        if existing_field.lower() == field_lower:
                            fields_to_remove.append(existing_field)
                
                # Remove the matched fields
                for field_to_remove in fields_to_remove:
                    if field_to_remove in meta:
                        del meta[field_to_remove]
                        fields_cleared_for_file += 1
                        cleared_count += 1
                
                if self.verbose and fields_cleared_for_file > 0:
                    self.log(f"Cleared {fields_cleared_for_file} fields from {file_entry.get('name', 'unknown')}")
        
        return cleared_count
    
    # Backup functionality removed to prevent .bak files
    
    def _write_json_file(self, json_path: Path, data: dict) -> None:
        """Write JSON data back to file."""
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.handle_error(e, f"Writing file {json_path}")
    
    def _print_summary(self, cleared_count: int, fields_to_clear: list, json_path: Path) -> None:
        """Print processing summary."""
        print(f"\n🧹 Metadata Clearing Complete:")
        print(f"   📄 File: {json_path}")
        
        if 'ALL' in fields_to_clear:
            print(f"   🗑️  Cleared: ALL metadata fields")
        else:
            print(f"   🗑️  Fields: {', '.join(fields_to_clear)}")
        
        print(f"   📊 Total cleared: {cleared_count} field occurrences")
        
        if hasattr(self.args, 'dry_run') and self.args.dry_run:
            print(f"   ⚠️  Mode: DRY RUN (no changes made)")
        else:
            print(f"   ✅ Changes saved to file")