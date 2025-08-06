"""
JSON Injection Module for strukt2meta

This module handles injecting AI-generated metadata into target JSON files
based on parameter configurations and schema definitions.
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List
from strukt2meta.apicall import call_ai_model


class JSONInjector:
    """Handles injection of AI-generated metadata into JSON files."""

    def __init__(self, params_file: str):
        """
        Initialize the injector with parameters from a JSON file.

        Args:
            params_file: Path to the parameter configuration file
        """
        self.params = self._load_params(params_file)
        self.backup_path = None

    def _load_params(self, params_file: str) -> Dict[str, Any]:
        """Load and validate parameter configuration."""
        if not os.path.exists(params_file):
            raise FileNotFoundError(f"Parameter file not found: {params_file}")


def inject_metadata_to_json(source_filename: str, metadata: Dict[str, Any], json_file_path: str, base_directory: str = None) -> bool:
    """
    Simple function to inject metadata directly into a JSON index file.

    Args:
        source_filename: Name of the source file
        metadata: Dictionary of metadata to inject
        json_file_path: Path to the JSON index file
        base_directory: Base directory (optional, for creating new JSON if needed)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Load existing JSON or create new structure
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        else:
            # Create new JSON structure
            json_data = {
                "files": [],
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }

        # Find existing file entry or create new one
        file_entry = None
        if 'files' in json_data:
            for entry in json_data['files']:
                if entry.get('name') == source_filename:
                    file_entry = entry
                    break

        if file_entry is None:
            # Create new file entry
            file_entry = {
                "name": source_filename,
                "meta": {}
            }
            if 'files' not in json_data:
                json_data['files'] = []
            json_data['files'].append(file_entry)

        # Inject metadata
        if 'meta' not in file_entry:
            file_entry['meta'] = {}

        # Update metadata fields
        for key, value in metadata.items():
            file_entry['meta'][key] = value

        # Update timestamp
        json_data['last_updated'] = datetime.now().isoformat()

        # Save JSON file
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)

        return True

    except Exception as e:
        print(f"Error injecting metadata: {e}")
        return False

        with open(params_file, 'r') as f:
            params = json.load(f)

        # Validate required parameters
        required_fields = ['input_path', 'prompt',
                           'json_inject_file', 'target_filename', 'injection_schema']
        for field in required_fields:
            if field not in params:
                raise ValueError(f"Required parameter missing: {field}")

        return params

    def _create_backup(self, json_file_path: str) -> str:
        """Create a backup of the target JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{json_file_path}.backup_{timestamp}"
        shutil.copy2(json_file_path, backup_path)
        self.backup_path = backup_path
        return backup_path

    def _load_target_json(self) -> Dict[str, Any]:
        """Load the target JSON file for injection."""
        json_file_path = self.params['json_inject_file']

        if not os.path.exists(json_file_path):
            raise FileNotFoundError(
                f"Target JSON file not found: {json_file_path}")

        # Create backup if enabled
        if self.params.get('backup_enabled', True):
            self._create_backup(json_file_path)

        with open(json_file_path, 'r') as f:
            return json.load(f)

    def _find_target_file_entry(self, json_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find the target file entry in the JSON structure."""
        target_filename = self.params['target_filename']

        # Search in files array
        if 'files' in json_data:
            for file_entry in json_data['files']:
                if file_entry.get('name') == target_filename:
                    return file_entry

        return None

    def _generate_metadata(self) -> Dict[str, Any]:
        """Generate metadata using AI model based on input and prompt."""
        input_path = self.params['input_path']
        prompt_name = self.params['prompt']

        # Read input file
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        with open(input_path, 'r') as f:
            input_text = f.read()

        # Load prompt
        prompts_dir = "./prompts"
        prompt_path = os.path.join(prompts_dir, f"{prompt_name}.md")
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        with open(prompt_path, 'r') as f:
            prompt = f.read()

        # Add schema instruction to prompt
        schema_instruction = f"\n\nPlease return the response as JSON matching this schema: {json.dumps(self.params['injection_schema'], indent=2)}"
        full_prompt = prompt + schema_instruction

        # Call AI model
        result = call_ai_model(full_prompt, input_text,
                               verbose=False, json_cleanup=True)

        # Parse result if it's a string
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError as e:
                raise ValueError(f"AI response is not valid JSON: {e}")

        return result

    def _validate_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Validate generated metadata against the injection schema."""
        schema = self.params['injection_schema']

        # Basic validation - check if all required fields are present
        if 'meta' in schema:
            if 'meta' not in metadata:
                return False

            for field in schema['meta']:
                if field not in metadata['meta']:
                    return False

        return True

    def _inject_metadata(self, json_data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Inject metadata into the target file entry."""
        file_entry = self._find_target_file_entry(json_data)

        if file_entry is None:
            raise ValueError(
                f"Target file not found: {self.params['target_filename']}")

        # Create meta object if it doesn't exist
        if 'meta' not in file_entry:
            file_entry['meta'] = {}

        # Inject metadata fields
        if 'meta' in metadata:
            for field, value in metadata['meta'].items():
                file_entry['meta'][field] = value

        return json_data

    def _save_json(self, json_data: Dict[str, Any]) -> None:
        """Save the modified JSON data back to file."""
        json_file_path = self.params['json_inject_file']

        with open(json_file_path, 'w') as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)

    def rollback(self) -> bool:
        """Rollback to backup if available."""
        if self.backup_path and os.path.exists(self.backup_path):
            shutil.copy2(self.backup_path, self.params['json_inject_file'])
            return True
        return False

    def inject(self) -> Dict[str, Any]:
        """
        Execute the complete injection process.

        Returns:
            Dictionary with operation results and metadata
        """
        try:
            # Load target JSON
            json_data = self._load_target_json()

            # Generate metadata
            print(f"Generating metadata for: {self.params['target_filename']}")
            metadata = self._generate_metadata()

            # Validate metadata
            if self.params.get('validation_strict', True):
                if not self._validate_metadata(metadata):
                    raise ValueError(
                        "Generated metadata does not match required schema")

            # Inject metadata
            modified_json = self._inject_metadata(json_data, metadata)

            # Save modified JSON
            self._save_json(modified_json)

            print(
                f"Successfully injected metadata into: {self.params['json_inject_file']}")

            return {
                'success': True,
                'target_file': self.params['target_filename'],
                'injected_metadata': metadata,
                'backup_path': self.backup_path
            }

        except Exception as e:
            print(f"Error during injection: {e}")
            if self.params.get('backup_enabled', True):
                print("Attempting rollback...")
                if self.rollback():
                    print("Rollback successful")
                else:
                    print("Rollback failed")
            raise
