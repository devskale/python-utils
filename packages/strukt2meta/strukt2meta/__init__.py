# This file makes the strukt2meta directory a Python package.

from .commands.base import BaseCommand
from .apicall import call_ai_model
from .jsonclean import cleanify_json
from .api import (
    load_prompt as api_load_prompt,
    generate_metadata_from_text,
    generate_metadata_from_file,
    discover_files,
    analyze_file,
    dirmeta_process,
    inject_with_params,
    inject_metadata,
    Strukt2Meta,
    FileDiscovery,
    FileMapping,
)

# For backward compatibility, create standalone functions
def query_ai_model(prompt: str, input_text: str, verbose: bool = False, json_cleanup: bool = False):
    """Backward compatibility wrapper for query_ai_model."""
    return call_ai_model(prompt, input_text, verbose, json_cleanup)

def load_prompt(prompt_name: str) -> str:
    """Backward compatibility wrapper for prompt loading."""
    return api_load_prompt(prompt_name)

__version__ = "0.1.1"
__all__ = [
    "query_ai_model",
    "load_prompt",
    "call_ai_model",
    "cleanify_json",
    "BaseCommand",
    # Programmatic API
    "generate_metadata_from_text",
    "generate_metadata_from_file",
    "discover_files",
    "analyze_file",
    "dirmeta_process",
    "inject_with_params",
    "inject_metadata",
    "Strukt2Meta",
    "FileDiscovery",
    "FileMapping",
]