"""Programmatic API for strukt2meta.

This module exposes high-level functions so other Python packages can use
strukt2meta without invoking the CLI. Functions intentionally avoid printing
to stdout (except optional verbose informational logs) and return structured
Python objects.

Design principles:
1. Zero mandatory side‑effects beyond what the caller requests (writing sidecars / index only when explicitly called).
2. Clear, typed return values (dict / list / dataclass instances).
3. Reuse existing internal logic (FileDiscovery, injector helpers, AI call).
4. Accept plain text OR file paths for generation.

Public Functions:
    load_prompt(prompt_name_or_path) -> str
    generate_metadata_from_text(prompt_name, text, *, json_cleanup=False, verbose=False, task_type='default')
    generate_metadata_from_file(file_path, prompt_name, *, json_cleanup=False, verbose=False, task_type='default')
    discover_files(directory, config_path=None) -> list[FileMapping]
    analyze_file(directory, source_filename, *, prompt='metadata_extraction', json_file=None, config_path=None, verbose=False)
    dirmeta_process(directory, prompt, *, json_file=None, overwrite=False, json_cleanup=False, verbose=False) -> dict
    inject_with_params(params_file) -> dict
    inject_metadata(source_filename, metadata, json_index_path, *, base_directory=None) -> bool

All functions raise exceptions on fatal errors (FileNotFoundError, ValueError, etc.).
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Union
import json
import os

from .apicall import call_ai_model
from .file_discovery import FileDiscovery, FileMapping
from .injector import inject_metadata_to_json, JSONInjector
from .jsonclean import cleanify_json

__all__ = [
    "load_prompt",
    "generate_metadata_from_text",
    "generate_metadata_from_file",
    "discover_files",
    "analyze_file",
    "dirmeta_process",
    "inject_with_params",
    "inject_metadata",
    "FileDiscovery",
    "FileMapping",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_prompt(prompt_name_or_path: str) -> str:
    """Load a prompt.

    If the value points to an existing file (any extension), it's read directly.
    Otherwise it is interpreted as a prompt name located in ./prompts/<name>.md
    relative to the current working directory.
    """
    candidate = Path(prompt_name_or_path)
    if candidate.exists() and candidate.is_file():
        return candidate.read_text(encoding="utf-8")

    # Treat as canonical prompt name (strip .md if provided)
    name = prompt_name_or_path[:-3] if prompt_name_or_path.endswith(".md") else prompt_name_or_path
    path = Path("prompts") / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


def _ensure_dict(result: Union[Dict[str, Any], str], *, json_cleanup: bool) -> Dict[str, Any]:
    """Normalize AI result into a dictionary.

    If result is a string, optionally run cleanify_json (repair) first.
    Fallback: wrap raw string in {'content': <string>}.
    """
    if isinstance(result, dict):
        return result
    if isinstance(result, str):
        if json_cleanup:
            try:
                repaired = cleanify_json(result)
                if isinstance(repaired, dict):
                    return repaired
                # If repaired returns list or primitive, wrap
                return {"data": repaired}
            except Exception:
                # Continue to JSON parse attempt
                pass
        try:
            parsed = json.loads(result)
            if isinstance(parsed, dict):
                return parsed
            return {"data": parsed}
        except Exception:
            return {"content": result}
    # Unexpected type
    return {"data": result}


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def generate_metadata_from_text(
    prompt_name: str,
    text: str,
    *,
    json_cleanup: bool = False,
    verbose: bool = False,
    task_type: str = "default",
) -> Dict[str, Any]:
    """Generate metadata from raw text using a named prompt.

    Args:
        prompt_name: Prompt name or path to prompt file.
        text: Source text to analyze.
        json_cleanup: Attempt to repair JSON and coerce to dict.
        verbose: Stream model output.
        task_type: Custom model selector ("default" or "kriterien").

    Returns:
        Dictionary with the AI-generated metadata (best-effort normalization).
    """
    prompt = load_prompt(prompt_name)
    result = call_ai_model(prompt, text, verbose=verbose, json_cleanup=json_cleanup, task_type=task_type)
    return _ensure_dict(result, json_cleanup=json_cleanup)


def generate_metadata_from_file(
    file_path: str | Path,
    prompt_name: str,
    *,
    json_cleanup: bool = False,
    verbose: bool = False,
    task_type: str = "default",
    encoding: str = "utf-8",
) -> Dict[str, Any]:
    """Generate metadata from a file's contents.

    Args mirror generate_metadata_from_text with an added file_path parameter.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    text = path.read_text(encoding=encoding)
    return generate_metadata_from_text(prompt_name, text, json_cleanup=json_cleanup, verbose=verbose, task_type=task_type)


# ---------------------------------------------------------------------------
# Discovery & Analysis
# ---------------------------------------------------------------------------
def discover_files(directory: str | Path, config_path: str | Path | None = None) -> List[FileMapping]:
    """Discover source files and markdown strukts.

    Returns the list of FileMapping objects (dataclass instances)."""
    discovery = FileDiscovery(str(directory), str(config_path) if config_path else None)
    return discovery.discover_files()


def analyze_file(
    directory: str | Path,
    source_filename: str,
    *,
    prompt: str = "metadata_extraction",
    json_file: str | None = None,
    config_path: str | None = None,
    verbose: bool = False,
    json_cleanup: bool = True,
) -> Dict[str, Any]:
    """Analyze a specific file inside a directory.

    Returns a dict that includes:
        metadata: parsed AI result
        meta_status: 'exists' | 'none'
        best_markdown: path to markdown used
        parser_used: parser label (if inferable)
    """
    discovery = FileDiscovery(str(directory), config_path)
    best_md = discovery.get_best_markdown_for_file(source_filename)
    if not best_md:
        raise FileNotFoundError(f"No markdown variant found for {source_filename}")
    # Determine metadata existence
    meta_status = discovery.check_metadata_exists(source_filename, json_file)
    text = Path(best_md).read_text(encoding="utf-8")
    metadata = generate_metadata_from_text(prompt, text, json_cleanup=json_cleanup, verbose=verbose)
    # Try to locate the mapping for parser info
    parser_used = None
    for mapping in discovery.discover_files():
        if mapping.source_file == source_filename:
            parser_used = mapping.parser_used
            break
    return {
        "metadata": metadata,
        "meta_status": meta_status,
        "best_markdown": best_md,
        "parser_used": parser_used,
    }


# ---------------------------------------------------------------------------
# Directory Metadata (dirmeta equivalent)
# ---------------------------------------------------------------------------
def dirmeta_process(
    directory: str | Path,
    prompt: str,
    *,
    json_file: str | None = None,
    overwrite: bool = False,
    json_cleanup: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Process an entire directory similar to the CLI 'dirmeta' command.

    Returns summary dict with keys:
        processed: list[str] filenames successfully processed
        failed: list[str] filenames that errored
        skipped: list[str] filenames skipped (existing metadata & not overwrite)
        json_index: path to index file used
    """
    directory_path = Path(directory)
    if not directory_path.exists() or not directory_path.is_dir():
        raise NotADirectoryError(f"Directory not found: {directory_path}")

    discovery = FileDiscovery(str(directory_path))
    mappings = discovery.discover_files()

    # Determine JSON index path (replicates CLI logic)
    if json_file:
        json_index_path = Path(json_file)
    else:
        index_file_name = ".ofs.index.json"
        try:
            cfg_path = Path("config.json")
            if cfg_path.exists():
                cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
                index_file_name = cfg.get("index_file_name", index_file_name)
        except Exception:
            pass
        candidate = directory_path / index_file_name
        legacy = directory_path / ".pdf2md_index.json"
        json_index_path = legacy if (not candidate.exists() and legacy.exists()) else candidate

    processed: List[str] = []
    failed: List[str] = []
    skipped: List[str] = []

    for mapping in mappings:
        if not mapping.best_markdown:
            continue
        # Skip existing metadata unless overwrite
        status = discovery.check_metadata_exists(mapping.source_file, str(json_index_path))
        if status == "exists" and not overwrite:
            skipped.append(mapping.source_file)
            continue
        try:
            md_text = (discovery.md_directory / mapping.best_markdown).read_text(encoding="utf-8")
            md_result = generate_metadata_from_text(prompt, md_text, json_cleanup=json_cleanup, verbose=verbose)
            # Inject selective fields + sidecar
            ok = inject_metadata_to_json(
                source_filename=mapping.source_file,
                metadata=md_result,
                json_file_path=str(json_index_path),
                base_directory=str(directory_path),
            )
            if ok:
                processed.append(mapping.source_file)
            else:
                failed.append(mapping.source_file)
        except Exception:
            failed.append(mapping.source_file)
            if verbose:
                import traceback; traceback.print_exc()

    return {
        "processed": processed,
        "failed": failed,
        "skipped": skipped,
        "json_index": str(json_index_path),
    }


# ---------------------------------------------------------------------------
# Injection
# ---------------------------------------------------------------------------
def inject_with_params(params_file: str | Path) -> Dict[str, Any]:
    """Execute a JSONInjector using a params file and return its result.

    Mirrors CLI 'inject' (non-dry-run)."""
    injector = JSONInjector(str(params_file))
    return injector.inject()


def inject_metadata(
    source_filename: str,
    metadata: Dict[str, Any],
    json_index_path: str | Path,
    *,
    base_directory: str | Path | None = None,
) -> bool:
    """Inject metadata directly (sidecar + selective index fields)."""
    return inject_metadata_to_json(
        source_filename=source_filename,
        metadata=metadata,
        json_file_path=str(json_index_path),
        base_directory=str(base_directory) if base_directory else None,
    )


# ---------------------------------------------------------------------------
# Convenience facade class (optional usage)
# ---------------------------------------------------------------------------
class Strukt2Meta:
    """Optional object-oriented facade bundling common operations."""

    def __init__(self, *, verbose: bool = False):
        self.verbose = verbose

    def generate_from_file(self, file_path: str | Path, prompt: str, **kw) -> Dict[str, Any]:
        return generate_metadata_from_file(file_path, prompt, verbose=self.verbose, **kw)

    def generate_from_text(self, prompt: str, text: str, **kw) -> Dict[str, Any]:
        return generate_metadata_from_text(prompt, text, verbose=self.verbose, **kw)

    def discover(self, directory: str | Path, config_path: str | Path | None = None) -> List[FileMapping]:
        return discover_files(directory, config_path)

    def analyze(self, directory: str | Path, source_filename: str, **kw) -> Dict[str, Any]:
        kw.setdefault("verbose", self.verbose)
        return analyze_file(directory, source_filename, **kw)

    def dirmeta(self, directory: str | Path, prompt: str, **kw) -> Dict[str, Any]:
        kw.setdefault("verbose", self.verbose)
        return dirmeta_process(directory, prompt, **kw)

    def inject(self, source_filename: str, metadata: Dict[str, Any], json_index_path: str | Path, **kw) -> bool:
        return inject_metadata(source_filename, metadata, json_index_path, **kw)

    def inject_params(self, params_file: str | Path) -> Dict[str, Any]:
        return inject_with_params(params_file)
