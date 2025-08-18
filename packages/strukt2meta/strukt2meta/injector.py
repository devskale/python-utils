"""
JSON Injection Module for strukt2meta (reworked)

Behavior changes:
- Always write a sidecar metadata file next to the source file:
    <source_filename>.meta.json
  This sidecar contains the full generated metadata.
- Only push a configurable subset of metadata fields into the index JSON
  (default: ["name", "kategorie", "begründung"]).
  These fields can be provided via:
    - JSONInjector params: "index_meta_fields"
    - a config.json at repository/base_directory containing "index_meta_fields"
    - fallback to the built-in default
- Backups of modified index files are created before writing.
- Backwards-compatible helper function `inject_metadata_to_json` updated
  to perform sidecar creation + selective index injection.
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from strukt2meta.apicall import call_ai_model


DEFAULT_INDEX_META_FIELDS = ["name", "kategorie", "begründung"]


def _load_index_meta_fields_from_config(base_dir: Optional[str] = None) -> List[str]:
    """
    Try to load index_meta_fields from a config.json file. Search order:
    1. If base_dir provided: base_dir/config.json
    2. cwd/config.json
    If not present or invalid, return the DEFAULT_INDEX_META_FIELDS.
    """
    candidates = []
    if base_dir:
        candidates.append(Path(base_dir) / "config.json")
    candidates.append(Path("config.json"))
    for cfg in candidates:
        try:
            if cfg.exists():
                with open(cfg, "r", encoding="utf-8") as f:
                    data = json.load(f)
                fields = data.get("index_meta_fields")
                if isinstance(fields, list) and all(isinstance(x, str) for x in fields):
                    return fields
        except Exception:
            # ignore and continue to next candidate
            pass
    return DEFAULT_INDEX_META_FIELDS


class JSONInjector:
    """Schema-driven AI metadata generator + injector with sidecar + selective index push."""

    REQUIRED_FIELDS = [
        'input_path', 'prompt', 'json_inject_file', 'target_filename', 'injection_schema'
    ]

    def __init__(self, params_file: str):
        self.params_file = params_file
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

    # --------------------------- Sidecar helpers ---------------------------
    def _sidecar_path_for_target(self) -> Path:
        """
        Decide where to write the sidecar metadata file.
        Default: same directory as `input_path`, filename "<target_filename>.meta.json"
        """
        input_path = Path(self.params['input_path'])
        sidecar_dir = input_path.parent if input_path.exists() else Path.cwd()
        sidecar_name = f"{self.params['target_filename']}.meta.json"
        return sidecar_dir / sidecar_name

    def _save_sidecar(self, metadata: Dict[str, Any]) -> Path:
        """
        Write the full metadata to the sidecar path and return the path.
        """
        sidecar = self._sidecar_path_for_target()
        try:
            sidecar.parent.mkdir(parents=True, exist_ok=True)
            with open(sidecar, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)
            return sidecar
        except Exception as e:
            raise RuntimeError(f"Failed to write sidecar file {sidecar}: {e}")

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

        result = call_ai_model(full_prompt, input_text, verbose=False, json_cleanup=True)
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError as e:
                raise ValueError(f"AI response not JSON: {e}")
        if not isinstance(result, dict):
            raise ValueError("AI response must be a JSON object")
        return result

    def _normalize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure metadata matches the schema shape (wrap flat keys into meta).
        Behavior preserved from previous implementation.
        """
        try:
            schema_meta = self.params.get('injection_schema', {}).get('meta', {})
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

    # --------------------------- Injection (sidecar + selective index) ---------------------------
    def _find_target_file_entry(self, json_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for entry in json_data.get('files', []):
            if entry.get('name') == self.params['target_filename']:
                return entry
        return None

    def _upsert_file_entry(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        entry = self._find_target_file_entry(json_data)
        if entry is None:
            entry = {"name": self.params['target_filename'], "meta": {}}
            json_data.setdefault('files', []).append(entry)
        if 'meta' not in entry:
            entry['meta'] = {}
        return entry

    def _apply_selected_to_entry(self, entry: Dict[str, Any], full_metadata: Dict[str, Any], index_fields: List[str]) -> List[str]:
        """
        Apply only the selected fields from full_metadata into the entry['meta'].
        Return a list of applied keys.
        full_metadata may have a 'meta' sub-dict or be flat.
        """
        applied = []
        source_meta = {}
        if isinstance(full_metadata, dict):
            if 'meta' in full_metadata and isinstance(full_metadata['meta'], dict):
                source_meta = full_metadata['meta']
            else:
                source_meta = full_metadata
        for key in index_fields:
            if key in source_meta:
                entry.setdefault('meta', {})[key] = source_meta[key]
                applied.append(key)
        return applied

    def _save_index(self, json_data: Dict[str, Any]) -> None:
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
        """
        Main entry point used by batch command.
        Writes full metadata to sidecar and selectively pushes configured fields into index.
        """
        json_data = self._load_target_json()
        raw_metadata = self._generate_metadata()
        metadata = self._normalize_metadata(raw_metadata)
        if self.params.get('validation_strict', True):
            if not self._validate_metadata(metadata):
                raise ValueError('Metadata failed validation against schema')

        # Write full metadata to sidecar
        sidecar_path = self._save_sidecar(metadata)

        # Determine fields to push into index (priority: params -> config -> default)
        index_fields = self.params.get('index_meta_fields')
        if not index_fields:
            index_fields = _load_index_meta_fields_from_config(base_dir=str(Path(self.params['input_path']).parent))
        if not isinstance(index_fields, list) or not all(isinstance(x, str) for x in index_fields):
            index_fields = DEFAULT_INDEX_META_FIELDS

        # Only push to index if any of the selected fields exist in metadata
        # (metadata may be {'meta': {...}} or a flat dict)
        source_meta = metadata['meta'] if isinstance(metadata, dict) and 'meta' in metadata else metadata
        if any(f in source_meta for f in index_fields):
            entry = self._upsert_file_entry(json_data)
            applied = self._apply_selected_to_entry(entry, metadata, index_fields)
            self._save_index(json_data)
        else:
            applied = []

        return {
            'success': True,
            'target_file': self.params['target_filename'],
            'sidecar_path': str(sidecar_path),
            'applied_index_fields': applied,
            'backup_path': self.backup_path
        }


# --------------------------- helper function (used by dirmeta / others) ---------------------------
def inject_metadata_to_json(source_filename: str, metadata: Dict[str, Any], json_file_path: str, base_directory: str | None = None) -> bool:
    """
    Simplified helper for direct metadata insertion (used by dirmeta / dirmeta-like flows).

    Behavior:
    - Write full metadata to sidecar: <base_directory>/<source_filename>.meta.json
      (if base_directory is None, write in cwd)
    - Load or create the index file at json_file_path (backing it up first if exists)
    - Push only configured index_meta_fields into the entry for source_filename
      (fields determined by config.json in base_directory or DEFAULT_INDEX_META_FIELDS)
    - Return True on success, False on failure.
    """
    try:
        # Normalize base_directory
        if base_directory:
            base_dir = Path(base_directory)
        else:
            base_dir = Path.cwd()

        # Ensure metadata shape: allow {'meta': {...}} or flat dict
        # Save sidecar next to base_directory / source_filename.meta.json
        sidecar_path = base_dir / f"{source_filename}.meta.json"
        try:
            sidecar_path.parent.mkdir(parents=True, exist_ok=True)
            with open(sidecar_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error writing sidecar file {sidecar_path}: {e}")
            # proceed: sidecar writing shouldn't prevent index push attempts

        # Load or initialize index JSON
        if os.path.exists(json_file_path):
            # Backup existing index
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = f"{json_file_path}.bak_{timestamp}"
                shutil.copy2(json_file_path, backup_path)
            except Exception:
                backup_path = None
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {"files": [], "created": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()}
            backup_path = None

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

        # Determine which fields to push to index
        index_fields = _load_index_meta_fields_from_config(base_dir=str(base_dir))
        # also allow override via environment variable (comma-separated)
        env_override = os.environ.get('STRUKT2META_INDEX_FIELDS')
        if env_override:
            try:
                env_fields = [x.strip() for x in env_override.split(',') if x.strip()]
                if env_fields:
                    index_fields = env_fields
            except Exception:
                pass

        # Determine source_meta dict to read from
        source_meta = {}
        if isinstance(metadata, dict):
            if 'meta' in metadata and isinstance(metadata['meta'], dict):
                source_meta = metadata['meta']
            else:
                source_meta = metadata

        # Apply only selected fields that exist in source_meta
        applied_any = False
        for key in index_fields:
            if key in source_meta:
                entry['meta'][key] = source_meta[key]
                applied_any = True

        # Only write index if we applied at least one field
        if applied_any:
            data['last_updated'] = datetime.now().isoformat()
            try:
                with open(json_file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"Error writing index file {json_file_path}: {e}")
                # attempt restore backup if available
                if backup_path:
                    try:
                        shutil.copy2(backup_path, json_file_path)
                    except Exception:
                        pass
                return False

        # Done: sidecar written (even if index unchanged)
        return True
    except Exception as e:
        print(f"Error injecting metadata: {e}")
        return False
