# This file makes the strukt2meta directory a Python package.

from .commands.base import BaseCommand
from .apicall import call_ai_model
from .jsonclean import cleanify_json

# For backward compatibility, create standalone functions
def query_ai_model(prompt: str, input_text: str, verbose: bool = False, json_cleanup: bool = False):
    """Backward compatibility wrapper for query_ai_model."""
    return call_ai_model(prompt, input_text, verbose, json_cleanup)

def load_prompt(prompt_name: str) -> str:
    """Backward compatibility wrapper for load_prompt."""
    import os
    prompts_dir = "./prompts"
    prompt_path = os.path.join(prompts_dir, f"{prompt_name}.md")
    
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    with open(prompt_path, "r", encoding="utf-8") as prompt_file:
        return prompt_file.read()

__version__ = "0.1.0"
__all__ = ["query_ai_model", "load_prompt", "call_ai_model", "cleanify_json", "BaseCommand"]