"""
Generate command handler for creating metadata from strukt files.
"""

import json
from .base import BaseCommand


class GenerateCommand(BaseCommand):
    """Handle the generate command (original functionality)."""
    
    def run(self) -> None:
        """Execute the generate command to create metadata from strukt file."""
        # Validate input file
        input_path = self.validate_file_path(self.args.i)
        
        # Read the input file
        with open(input_path, "r", encoding="utf-8") as infile:
            input_text = infile.read()
            self.log(f"Input text loaded from: {input_path}")

        # Load the prompt
        prompt = self.load_prompt(self.args.p)
        self.log(f"Using prompt: {self.args.p}")

        # Query the AI model
        result = self.query_ai_model(
            prompt, 
            input_text, 
            verbose=self.args.verbose, 
            json_cleanup=getattr(self.args, 'j', False)
        )

        # Write the result to the output file
        output_path = self.validate_file_path(self.args.o, must_exist=False)
        with open(output_path, "w", encoding="utf-8") as outfile:
            json.dump(result, outfile, indent=4, ensure_ascii=False)
            self.log(f"Output written to: {output_path}", "success")