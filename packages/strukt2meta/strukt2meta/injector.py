"""
JSON Injection Module for strukt2meta

Provides two paths:
1. JSONInjector class: schema-driven generation + injection (used by batch command)
2. inject_metadata_to_json helper: simple direct metadata insertion (used by dirmeta)
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any, Optional

from strukt2meta.apicall import call_ai_model


class JSONInjector:
    """Schema-driven AI metadata generator + injector."""

    REQUIRED_FIELDS = [
        'input_path', 'prompt', 'json_inject_file', 'target_filename', 'injection_schema'
    ]

    def __init__(self, params_file: str):
        self.params = self._load_params(params_file)
        self.backup_path: Optional[str] = None

    # --------------------------- Param + IO helpers ---------------------------
    def _load_params(self, params_file: str) -> Dict[str, Any]:
        if not os.path.exists(params_file):
            raise FileNotFoundError(f"Parameter file not found: {params_file}")
        with open(params_file, 'r', encoding='utf-8') as f:
            params = json.load(f)
        for field in self.REQUIRED_FIELDS:
            if field not in params:
                raise ValueError(f"Required parameter missing: {field}")
        return params

    def _create_backup(self, json_file_path: str) -> None:
        if not os.path.exists(json_file_path):
            return
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{json_file_path}.bak_{timestamp}"
        shutil.copy2(json_file_path, backup_path)
        self.backup_path = backup_path

    def _load_target_json(self) -> Dict[str, Any]:
        target = self.params['json_inject_file']
        if not os.path.exists(target):
            # Initialize new index structure
            data = {"files": [], "created": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()}
            return data
        if self.params.get('backup_enabled', True):
            self._create_backup(target)
        with open(target, 'r', encoding='utf-8') as f:
            return json.load(f)

    # --------------------------- Discovery helpers ---------------------------
    def _find_target_file_entry(self, json_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for entry in json_data.get('files', []):
            if entry.get('name') == self.params['target_filename']:
                return entry
        return None

    # --------------------------- AI Generation ---------------------------
    def _generate_metadata(self) -> Dict[str, Any]:
        input_path = self.params['input_path']
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        with open(input_path, 'r', encoding='utf-8') as f:
            input_text = f.read()

        prompt_name = self.params['prompt']
        prompt_path = os.path.join('prompts', f'{prompt_name}.md')
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        with open(prompt_path, 'r', encoding='utf-8') as f:
            base_prompt = f.read()

        schema_instruction = "\n\nReturn valid JSON following this schema (omit explanation text):\n" + json.dumps(
            self.params['injection_schema'], indent=2, ensure_ascii=False)
        full_prompt = base_prompt + schema_instruction

        result = call_ai_model(full_prompt, input_text,
                               verbose=False, json_cleanup=True)
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError as e:
                raise ValueError(f"AI response not JSON: {e}")
        if not isinstance(result, dict):
            raise ValueError("AI response must be a JSON object")
        return result

    def _normalize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure metadata matches the schema shape (wrap flat keys into meta)."""
        try:
            schema_meta = self.params.get(
                'injection_schema', {}).get('meta', {})
            # If already has 'meta' dict, keep it
            if 'meta' in metadata and isinstance(metadata['meta'], dict):
                return metadata
            # Collect expected fields at top-level
            collected = {}
            for field in schema_meta.keys():
                if field in metadata:
                    collected[field] = metadata[field]
            if collected:
                return {'meta': collected}
            # If nothing matched, but metadata is a flat dict, still wrap everything to avoid validation failure
            # (Only if schema expects meta)
            if schema_meta and all(not isinstance(v, dict) for v in metadata.values()):
                return {'meta': metadata}
            return metadata
        except Exception:
            return metadata

    def _validate_metadata(self, metadata: Dict[str, Any]) -> bool:
        schema = self.params['injection_schema']
        if 'meta' in schema:
            if 'meta' not in metadata or not isinstance(metadata['meta'], dict):
                return False
            # Optional: ensure at least one expected key present
            expected = list(schema['meta'].keys())
            if expected:
                if not any(k in metadata['meta'] for k in expected):
                    return False
        return True

    # --------------------------- Injection ---------------------------
    def _upsert_file_entry(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        entry = self._find_target_file_entry(json_data)
        if entry is None:
            entry = {"name": self.params['target_filename'], "meta": {}}
            json_data.setdefault('files', []).append(entry)
        if 'meta' not in entry:
            entry['meta'] = {}
        return entry

    def _apply_metadata(self, entry: Dict[str, Any], metadata: Dict[str, Any]) -> None:
        # Allow metadata to either be a flat dict of fields (meta-level) or {'meta': {...}}
        if 'meta' in metadata and isinstance(metadata['meta'], dict):
            for k, v in metadata['meta'].items():
                entry['meta'][k] = v
        else:
            for k, v in metadata.items():
                entry['meta'][k] = v

    def _save(self, json_data: Dict[str, Any]) -> None:
        target = self.params['json_inject_file']
        json_data['last_updated'] = datetime.now().isoformat()
        with open(target, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)

    def rollback(self) -> bool:
        if self.backup_path and os.path.exists(self.backup_path):
            shutil.copy2(self.backup_path, self.params['json_inject_file'])
            return True
        return False

    def inject(self) -> Dict[str, Any]:
        """Main entry point used by batch command."""
        json_data = self._load_target_json()
        raw_metadata = self._generate_metadata()
        metadata = self._normalize_metadata(raw_metadata)
        if self.params.get('validation_strict', True):
            if not self._validate_metadata(metadata):
                raise ValueError('Metadata failed validation against schema')
        entry = self._upsert_file_entry(json_data)
        self._apply_metadata(entry, metadata)
        self._save(json_data)
        return {
            'success': True,
            'target_file': self.params['target_filename'],
            'metadata_keys': list(entry['meta'].keys()),
            'backup_path': self.backup_path
        }


def inject_metadata_to_json(source_filename: str, metadata: Dict[str, Any], json_file_path: str, base_directory: str | None = None) -> bool:
    """Simplified helper for direct metadata insertion (used by dirmeta)."""
    try:
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {"files": [], "created": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()}

        # Locate / create file entry
        entry = None
        for e in data.get('files', []):
            if e.get('name') == source_filename:
                entry = e
                break
        if entry is None:
            entry = {"name": source_filename, "meta": {}}
            data.setdefault('files', []).append(entry)
        if 'meta' not in entry:
            entry['meta'] = {}

        # Merge metadata
        for k, v in metadata.items():
            entry['meta'][k] = v

        data['last_updated'] = datetime.now().isoformat()
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error injecting metadata: {e}")
        return False
