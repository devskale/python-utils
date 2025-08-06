"""
Discover command handler for file discovery and parser rankings.
"""

from .base import BaseCommand


class DiscoverCommand(BaseCommand):
    """Handle the discover command for file discovery."""
    
    def run(self) -> None:
        """Execute the discover command to find and rank files."""
        from strukt2meta.file_discovery import FileDiscovery

        try:
            # Validate directory
            directory_path = self.validate_directory_path(self.args.directory)
            
            if self.verbose:
                self.log(f"Discovering files in: {directory_path}", "search")

            discovery = FileDiscovery(str(directory_path), self.args.config)
            discovery.print_discovery_report()

        except Exception as e:
            self.log(f"Error during file discovery: {e}", "error")
            raise