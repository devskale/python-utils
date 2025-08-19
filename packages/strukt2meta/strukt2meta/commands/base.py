"""
Base command class with common functionality for all command handlers.
"""

import os
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, Union, Optional
from strukt2meta.apicall import call_ai_model


class CommandError(Exception):
    """Custom exception for command-specific errors."""

    def __init__(self, message: str, error_code: int = 1):
        super().__init__(message)
        self.error_code = error_code


class BaseCommand:
    """Base class for command handlers with common functionality."""

    def __init__(self, args):
        """Initialize base command with parsed arguments."""
        self.args = args
        self.verbose = getattr(args, 'verbose', False)
        self.error_count = 0
        self.warning_count = 0

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

        # Track error and warning counts
        if level == "error":
            self.error_count += 1
        elif level == "warning":
            self.warning_count += 1

    def handle_error(self, error: Exception, context: str = "", fatal: bool = True) -> None:
        """Handle errors with consistent formatting and optional stack trace."""
        error_msg = f"Error in {context}: {str(error)}" if context else f"Error: {str(error)}"
        self.log(error_msg, "error")

        if self.verbose:
            self.log("Stack trace:", "error")
            traceback.print_exc()

        if fatal:
            sys.exit(1)

    def handle_warning(self, message: str, context: str = "") -> None:
        """Handle warnings with consistent formatting."""
        warning_msg = f"Warning in {context}: {message}" if context else f"Warning: {message}"
        self.log(warning_msg, "warning")

    def validate_and_run(self) -> None:
        """Wrapper method that handles errors consistently across all commands."""
        try:
            self.run()
            self._print_execution_summary()
        except CommandError as e:
            self.handle_error(e, fatal=True)
        except FileNotFoundError as e:
            self.handle_error(e, "File operation", fatal=True)
        except PermissionError as e:
            self.handle_error(e, "Permission", fatal=True)
        except Exception as e:
            self.handle_error(e, "Unexpected error", fatal=True)

    def _print_execution_summary(self) -> None:
        """Print execution summary with error and warning counts."""
        if self.error_count > 0 or self.warning_count > 0:
            print("\n" + "="*50)
            print("EXECUTION SUMMARY")
            print("="*50)
            if self.error_count > 0:
                self.log(f"Total errors: {self.error_count}", "error")
            if self.warning_count > 0:
                self.log(f"Total warnings: {self.warning_count}", "warning")
            if self.error_count == 0:
                self.log("Execution completed with warnings", "warning")
        else:
            self.log("Execution completed successfully", "success")

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
                       verbose: bool = False, json_cleanup: bool = False, task_type: str = "default") -> Union[Dict, str]:
        """
        Query AI model with given prompt and input text.

        Args:
            prompt: The prompt template to use
            input_text: Input text to analyze
            verbose: Enable verbose output
            json_cleanup: Enable JSON cleanup
            task_type: Type of task for model configuration ("default", "kriterien")

        Returns:
            Analysis result as dict or string
        """
        return call_ai_model(prompt, input_text, verbose, json_cleanup, task_type)

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
