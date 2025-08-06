"""
Inject command handler for injecting metadata into JSON files.
"""

import json
from .base import BaseCommand


class InjectCommand(BaseCommand):
    """Handle the inject command for metadata injection."""
    
    def run(self) -> None:
        """Execute the inject command to inject metadata into JSON file."""
        from strukt2meta.injector import JSONInjector

        if self.verbose:
            self.log(f"Loading parameters from: {self.args.params}")

        injector = JSONInjector(self.args.params)

        if self.args.dry_run:
            self._handle_dry_run(injector)
            return

        # Execute injection
        result = injector.inject()

        if result['success']:
            self.log("Injection completed successfully!", "success")
            if self.verbose:
                self._log_injection_details(result)
        else:
            self.log("Injection failed", "error")
    
    def _handle_dry_run(self, injector) -> None:
        """Handle dry run mode for injection."""
        print("DRY RUN MODE - No files will be modified")
        print("Parameter validation: PASSED")
        print(f"Target file: {injector.params['target_filename']}")
        print(f"JSON file: {injector.params['json_inject_file']}")
        print(f"Input path: {injector.params['input_path']}")
        print(f"Prompt: {injector.params['prompt']}")
    
    def _log_injection_details(self, result: dict) -> None:
        """Log detailed injection results."""
        print(f"Target file: {result['target_file']}")
        print(f"Backup created: {result['backup_path']}")
        print("Injected metadata:")
        print(json.dumps(
            result['injected_metadata'], 
            indent=2, 
            ensure_ascii=False
        ))