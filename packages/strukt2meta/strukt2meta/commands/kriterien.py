"""Kriterien command handler for extracting criteria from tender documents.

This module implements the KriterienCommand class that extracts criteria
from tender documents (Ausschreibungsunterlagen) using AI models.
It supports both overwrite and insert modes for JSON output.
"""

import json
import os
import threading
import time
import sys
from typing import Dict, Any, Optional
from .base import BaseCommand
from strukt2meta.jsonclean import cleanify_json


class Spinner:
    """Visual spinner for long-running operations."""
    
    def __init__(self, message: str = "Processing"):
        """Initialize spinner with message.
        
        Args:
            message: Message to display alongside spinner
        """
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.message = message
        self.spinning = False
        self.thread = None

    def spin(self) -> None:
        """Run the spinner animation."""
        i = 0
        while self.spinning:
            sys.stdout.write(
                f'\r{self.message} {self.spinner_chars[i % len(self.spinner_chars)]}'
            )
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

    def start(self) -> None:
        """Start the spinner in a separate thread."""
        self.spinning = True
        self.thread = threading.Thread(target=self.spin)
        self.thread.start()

    def stop(self) -> None:
        """Stop the spinner and clean up display."""
        self.spinning = False
        if self.thread:
            self.thread.join()
        sys.stdout.write('\r' + ' ' * (len(self.message) + 2) + '\r')
        sys.stdout.flush()


class KriterienCommand(BaseCommand):
    """Handle the kriterien command for extracting criteria from tender documents."""
    
    def load_existing_json(self, file_path: str) -> Dict[str, Any]:
        """Load existing JSON file if it exists, otherwise return empty dict.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dictionary containing existing JSON data or empty dict
        """
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.log(f"Warning: Could not load existing JSON from {file_path}", "warning")
                return {}
        return {}
    
    def merge_json_with_insert(self, existing_data: Dict[str, Any], 
                              new_data: Dict[str, Any], 
                              insert_key: Optional[str]) -> Dict[str, Any]:
        """Merge new data into existing JSON, clearing only the specified key.
        
        Args:
            existing_data: Existing JSON data
            new_data: New data to merge
            insert_key: Specific key to replace, or None for full replacement
            
        Returns:
            Merged JSON data
        """
        if insert_key:
            # Clear only the specified key and replace with new data
            if insert_key in new_data:
                existing_data[insert_key] = new_data[insert_key]
                self.log(f"Cleared and updated '{insert_key}' section", "success")
            else:
                self.log(f"Warning: Key '{insert_key}' not found in new data", "warning")
        else:
            # Replace entire structure
            existing_data.update(new_data)
        return existing_data
    
    def run(self) -> None:
        """Execute the kriterien command to extract criteria from tender documents."""
        try:
            # Validate and read prompt file
            prompt_path = self.validate_file_path(self.args.prompt)
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_text = f.read()
            self.log(f"Prompt loaded from {prompt_path}")
            
            # Validate and read input file
            input_path = self.validate_file_path(self.args.file)
            with open(input_path, 'r', encoding='utf-8') as f:
                file_text = f.read()
            self.log(f"File loaded from {input_path} ({len(file_text):,} characters)")
            
            # Combine prompt and file content
            full_prompt = f"{prompt_text}\n\n---\n\n{file_text}"
            
            self.log(f"Sending request to AI model (Total: {len(full_prompt):,} characters)", "processing")
            
            # Show spinner for AI processing
            spinner = Spinner("🤖 Waiting for AI response")
            spinner.start()
            
            try:
                # Query AI model directly using apicall to avoid streaming
                from strukt2meta.apicall import call_ai_model
                response_text = call_ai_model(
                    prompt_text, 
                    file_text, 
                    verbose=False,  # Explicitly disable streaming
                    json_cleanup=False  # We'll handle JSON cleanup ourselves
                )
            finally:
                spinner.stop()
            
            self.log("Response received!", "success")
            
            # Process response
            self.log("Processing response...", "processing")
            if self.args.output.endswith('.json'):
                spinner = Spinner("📊 Cleaning JSON")
                spinner.start()
                try:
                    new_data = cleanify_json(response_text)
                finally:
                    spinner.stop()
            else:
                new_data = {"analysis_result": response_text}
            
            # Ensure output directory exists
            output_dir = os.path.dirname(self.args.output)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Handle insert mode vs overwrite mode
            if hasattr(self.args, 'insert') and self.args.insert:
                self.log(f"Insert mode: updating '{self.args.insert}' section...", "processing")
                existing_data = self.load_existing_json(self.args.output)
                final_data = self.merge_json_with_insert(existing_data, new_data, self.args.insert)
                self.log(f"Updating {self.args.output}...")
            else:
                self.log("Overwrite mode: creating new file...", "processing")
                final_data = new_data
                self.log(f"Saving to {self.args.output}...")
            
            # Write output file
            with open(self.args.output, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=4)
            
            self.log(f"Analysis complete! Output saved to {self.args.output}", "success")
            
            # Show statistics
            if isinstance(final_data, dict) and 'kriterien' in final_data:
                criteria_count = len(final_data['kriterien'])
                self.log(f"Extracted {criteria_count} criteria")
            
            file_size = os.path.getsize(self.args.output)
            self.log(f"File size: {file_size:,} bytes")
            
        except Exception as e:
            self.log(f"Error during kriterien extraction: {e}", "error")
            raise