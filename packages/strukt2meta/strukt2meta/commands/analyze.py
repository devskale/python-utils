"""
Analyze command handler for intelligent analysis of files.
"""

import json
from .base import BaseCommand


class AnalyzeCommand(BaseCommand):
    """Handle the analyze command for intelligent analysis."""
    
    def run(self) -> None:
        """Execute the analyze command for intelligent file analysis."""
        from strukt2meta.file_discovery import FileDiscovery

        # Validate directory
        directory_path = self.validate_directory_path(self.args.directory)
        
        discovery = FileDiscovery(str(directory_path), self.args.config)

        if self.args.file:
            self._analyze_specific_file(discovery)
        else:
            self._show_available_files(discovery)
    
    def _analyze_specific_file(self, discovery) -> None:
        """Analyze a specific file."""
        # Analyze specific file
        best_md = discovery.get_best_markdown_for_file(self.args.file)
        if not best_md:
            self.log(f"No markdown file found for: {self.args.file}", "error")
            return

        # Check if metadata already exists
        meta_status = discovery.check_metadata_exists(
            self.args.file, self.args.json_file)

        if self.verbose:
            self.log(f"Analyzing: {self.args.file}")
            self.log(f"Using markdown: {best_md}")
            self.log(f"Metadata status: {meta_status}")

        # Read and analyze the markdown file
        with open(best_md, "r", encoding="utf-8") as f:
            input_text = f.read()

        prompt = self.load_prompt(self.args.prompt)
        result = self.query_ai_model(prompt, input_text, verbose=self.verbose)

        # Add metadata existence status to the result
        result = self._add_meta_status(result, meta_status)

        if self.args.output:
            self._write_results_to_file(result)
        else:
            self._print_results(result)
    
    def _add_meta_status(self, result, meta_status: str):
        """Add metadata status to analysis result."""
        if isinstance(result, dict):
            result["meta_status"] = meta_status
        elif isinstance(result, str):
            # If result is a string, try to parse as JSON and add the field
            try:
                parsed_result = json.loads(result)
                if isinstance(parsed_result, dict):
                    parsed_result["meta_status"] = meta_status
                    result = json.dumps(
                        parsed_result, indent=2, ensure_ascii=False)
                else:
                    # If not a dict, create a wrapper
                    result = {
                        "analysis": result,
                        "meta_status": meta_status
                    }
            except json.JSONDecodeError:
                # If parsing fails, create a wrapper
                result = {
                    "analysis": result,
                    "meta_status": meta_status
                }
        else:
            result = {
                "analysis": str(result),
                "meta_status": meta_status
            }
        return result
    
    def _write_results_to_file(self, result) -> None:
        """Write analysis results to output file."""
        output_path = self.validate_file_path(self.args.output, must_exist=False)
        with open(output_path, "w", encoding="utf-8") as f:
            if isinstance(result, str):
                f.write(result)
            else:
                json.dump(result, f, indent=4, ensure_ascii=False)
        self.log(f"Results written to: {output_path}", "success")
    
    def _print_results(self, result) -> None:
        """Print analysis results to console."""
        print("📊 Analysis Results:")
        if isinstance(result, str):
            print(result)
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    def _show_available_files(self, discovery) -> None:
        """Show available files for analysis."""
        mappings = discovery.discover_files()
        print(f"📁 Found {len(mappings)} files available for analysis:")
        
        for mapping in mappings:
            status = "✅" if mapping.best_markdown else "❌"
            meta_status = discovery.check_metadata_exists(mapping.source_file)
            meta_icon = "🏷️" if meta_status == "exists" else "📝"
            
            print(f"   {status} {mapping.source_file} ({mapping.source_type}) "
                  f"{meta_icon} meta: {meta_status}")
            
            if mapping.best_markdown:
                print(f"      → {mapping.best_markdown} "
                      f"(confidence: {mapping.confidence_score:.2f})")