# This file makes the strukt2meta directory a Python package.

from .main import query_ai_model, load_prompt
from .apicall import call_ai_model
from .jsonclean import cleanify_json

__version__ = "0.1.0"
__all__ = ["query_ai_model", "load_prompt", "call_ai_model", "cleanify_json"]