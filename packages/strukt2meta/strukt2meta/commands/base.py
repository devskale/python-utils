"""
Base command class with common functionality for all command handlers.
"""

import os
from pathlib import Path
from typing import Any, Dict, Union
from strukt2meta.apicall import call_ai_model


class BaseCommand:
    """Base class for command handlers with common functionality."""
    
    def __init__(self, args):
        """Initialize base command with parsed arguments."""
        self.args = args
        self.verbose = getattr(args, 'verbose', False)
    
    def log(self, message: str, level: str = "info") -> None:
        """
        Unified logging method with emoji icons.
        
        Args:
            message: Message to log
            level: Log level (info, success, error, warning)
        """
        if self.verbose or level in ["error", "warning"]:
            icons = {
                "info": "ℹ️", 
                "success": "✅", 
                "error": "❌", 
                "warning": "⚠️",
                "processing": "🔄",
                "search": "🔍"
            }
            print(f"{icons.get(level, 'ℹ️')} {message}")
    
    def load_prompt(self, prompt_name: str) -> str:
        """
        Load prompt file with error handling.
        
        Args:
            prompt_name: Name of the prompt file (without .md extension)
            
        Returns:
            Content of the prompt file
            
        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        prompts_dir = "./prompts"
        prompt_path = os.path.join(prompts_dir, f"{prompt_name}.md")
        
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        
        with open(prompt_path, "r", encoding="utf-8") as prompt_file:
            return prompt_file.read()
    
    def query_ai_model(self, prompt: str, input_text: str, 
                      verbose: bool = False, json_cleanup: bool = False) -> Union[Dict, str]:
        """
        Query AI model with given prompt and input text.
        
        Args:
            prompt: The prompt template to use
            input_text: Input text to analyze
            verbose: Enable verbose output
            json_cleanup: Enable JSON cleanup
            
        Returns:
            Analysis result as dict or string
        """
        return call_ai_model(prompt, input_text, verbose, json_cleanup)
    
    def validate_file_path(self, path: str, must_exist: bool = True) -> Path:
        """
        Validate and return Path object with proper error handling.
        
        Args:
            path: File path to validate
            must_exist: Whether the file must exist
            
        Returns:
            Validated Path object
            
        Raises:
            FileNotFoundError: If file doesn't exist and must_exist is True
        """
        path_obj = Path(path)
        if must_exist and not path_obj.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return path_obj
    
    def validate_directory_path(self, path: str) -> Path:
        """
        Validate directory path.
        
        Args:
            path: Directory path to validate
            
        Returns:
            Validated Path object
            
        Raises:
            NotADirectoryError: If path is not a directory
            FileNotFoundError: If directory doesn't exist
        """
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        if not path_obj.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {path}")
        return path_obj
    
    def run(self) -> None:
        """
        Execute the command. Must be implemented by subclasses.
        
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement the run method")