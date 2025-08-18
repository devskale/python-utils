"""OFS command handler for processing files in Opinionated File System structure."""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import OFS package functions
try:
    import ofs
    from ofs import (
        list_projects, 
        list_bidders, 
        list_bidder_docs_json, 
        list_project_docs_json, 
        read_doc,
        get_path,
        find_bidder_in_project
    )
except ImportError:
    raise ImportError("OFS package not found. Please install it with: pip install -e ../ofs")

from .base import BaseCommand
from strukt2meta.injector import inject_metadata_to_json


class OfsCommand(BaseCommand):
    """Handle OFS command for processing files in Opinionated File System structure."""
    
    def run(self) -> None:
        """Execute the OFS command for processing OFS structured files."""
        # Parse the OFS parameter
        ofs_param = self.args.ofs
        project, bidder, filename = self._parse_ofs_parameter(ofs_param)
        
        self.log(f"Processing OFS parameter: {ofs_param}", "info")
        self.log(f"Parsed - Project: {project}, Bidder: {bidder}, File: {filename}", "info")
        
        # Determine processing scope and execute
        if filename:
            # Process single file
            self._process_single_file(project, bidder, filename)
        elif bidder:
            # Process all files for a specific bidder
            self._process_bidder_files(project, bidder)
        else:
            # Process all files in project (both A/ and B/ directories)
            self._process_project_files(project)
    
    def _parse_ofs_parameter(self, ofs_param: str) -> Tuple[str, Optional[str], Optional[str]]:
        """Parse OFS parameter into project, bidder, and filename components.
        
        Args:
            ofs_param: OFS parameter in format:
                - projectname (process all files)
                - projectname@filename (process project file in A/ directory)
                - projectname@biddername (process all bidder files)
                - projectname@biddername@filename (process specific bidder file)
            
        Returns:
            Tuple of (project, bidder, filename)
        """
        parts = ofs_param.split('@')
        
        project = parts[0] if parts else None
        
        if not project:
            raise ValueError("Project name is required in OFS parameter")
        
        if len(parts) == 1:
            # Just project name - process all files
            return project, None, None
        elif len(parts) == 2:
            # Could be project@filename or project@bidder
            # Check if second part is a known bidder
            try:
                bidders = list_bidders(project)
                if parts[1] in bidders:
                    # It's a bidder
                    return project, parts[1], None
                else:
                    # It's a filename in project A/ directory
                    return project, None, parts[1]
            except Exception:
                # If we can't check bidders, assume it's a filename
                return project, None, parts[1]
        elif len(parts) == 3:
            # project@bidder@filename
            return project, parts[1], parts[2]
        else:
            raise ValueError(f"Invalid OFS parameter format: {ofs_param}")
    
    def _process_single_file(self, project: str, bidder: Optional[str], filename: str) -> None:
        """Process a single file using OFS read_doc function.
        
        Args:
            project: Project name
            bidder: Bidder name (optional)
            filename: Filename to process
        """
        # Construct OFS identifier
        if bidder:
            identifier = f"{project}@{bidder}@{filename}"
        else:
            # For project files, use A as the "bidder" part
            identifier = f"{project}@A@{filename}"
        
        self.log(f"Processing single file: {identifier}", "processing")
        
        try:
            # Read document content using OFS
            doc_result = read_doc(identifier)
            
            # Check if doc_result is a dict with success/error structure or direct content
            if isinstance(doc_result, dict) and 'success' in doc_result:
                if not doc_result.get('success'):
                    self.log(f"Failed to read document: {doc_result.get('error', 'Unknown error')}", "error")
                    return
                content = doc_result.get('content', '')
                parser = doc_result.get('parser', 'unknown')
            else:
                # Direct content return
                content = doc_result if isinstance(doc_result, str) else str(doc_result)
                parser = 'ofs'
            
            self.log(f"Document read successfully using parser: {parser}", "success")
            
            # Determine prompt based on file location
            prompt_name = self._determine_prompt(project, bidder)
            
            # Generate metadata
            metadata = self._generate_metadata(content, prompt_name, identifier)
            
            if metadata:
                # Inject metadata into appropriate JSON file
                self._inject_metadata(metadata, project, bidder, filename)
                self.log(f"Successfully processed: {identifier}", "success")
            
        except Exception as e:
            self.log(f"Error processing {identifier}: {str(e)}", "error")
    
    def _process_bidder_files(self, project: str, bidder: str) -> None:
        """Process all files for a specific bidder.
        
        Args:
            project: Project name
            bidder: Bidder name
        """
        self.log(f"Processing all files for bidder: {project}@{bidder}", "processing")
        
        try:
            # Get list of bidder documents
            docs_result = list_bidder_docs_json(project, bidder)
            
            # Handle direct list return or wrapped result
            if isinstance(docs_result, dict) and 'success' in docs_result:
                if not docs_result.get('success'):
                    self.log(f"Failed to list bidder documents: {docs_result.get('error', 'Unknown error')}", "error")
                    return
                documents = docs_result.get('documents', [])
            elif isinstance(docs_result, dict) and 'documents' in docs_result:
                documents = docs_result.get('documents', [])
            elif isinstance(docs_result, list):
                documents = docs_result
            else:
                self.log(f"Unexpected result format from list_bidder_docs_json: {type(docs_result)}", "error")
                return
            
            if not documents:
                self.log(f"No documents found for bidder: {bidder}", "warning")
                return
            
            self.log(f"Found {len(documents)} documents for bidder: {bidder}", "info")
            
            # Process each document
            for doc in documents:
                filename = doc.get('name')
                if filename and self._should_process_file(doc):
                    self._process_single_file(project, bidder, filename)
                    
        except Exception as e:
            self.log(f"Error processing bidder files for {project}@{bidder}: {str(e)}", "error")
    
    def _process_project_files(self, project: str) -> None:
        """Process all files in a project (both A/ and B/ directories).
        
        Args:
            project: Project name
        """
        self.log(f"Processing all files for project: {project}", "processing")
        
        try:
            # Process project documents (A/ directory)
            self._process_project_documents(project)
            
            # Process all bidder documents (B/ directory)
            self._process_all_bidder_documents(project)
            
        except Exception as e:
            self.log(f"Error processing project files for {project}: {str(e)}", "error")
    
    def _process_project_documents(self, project: str) -> None:
        """Process documents in the project's A/ directory.
        
        Args:
            project: Project name
        """
        try:
            # Get list of project documents
            docs_result = list_project_docs_json(project)
            
            # Handle direct list return or wrapped result
            if isinstance(docs_result, dict) and 'success' in docs_result:
                if not docs_result.get('success'):
                    self.log(f"Failed to list project documents: {docs_result.get('error', 'Unknown error')}", "warning")
                    return
                documents = docs_result.get('documents', [])
            elif isinstance(docs_result, dict) and 'documents' in docs_result:
                documents = docs_result.get('documents', [])
            elif isinstance(docs_result, list):
                documents = docs_result
            else:
                self.log(f"Unexpected result format from list_project_docs_json: {type(docs_result)}", "warning")
                return
            
            if documents:
                self.log(f"Found {len(documents)} project documents", "info")
                
                for doc in documents:
                    filename = doc.get('name')
                    if filename and self._should_process_file(doc):
                        self._process_single_file(project, None, filename)
            
        except Exception as e:
            self.log(f"Error processing project documents for {project}: {str(e)}", "error")
    
    def _process_all_bidder_documents(self, project: str) -> None:
        """Process documents for all bidders in a project.
        
        Args:
            project: Project name
        """
        try:
            # Get list of bidders
            bidders = list_bidders(project)
            
            if not bidders:
                self.log(f"No bidders found for project: {project}", "info")
                return
            
            self.log(f"Found {len(bidders)} bidders in project: {project}", "info")
            
            # Process each bidder's documents
            for bidder in bidders:
                self._process_bidder_files(project, bidder)
                
        except Exception as e:
            self.log(f"Error processing bidder documents for {project}: {str(e)}", "error")
    
    def _should_process_file(self, doc: Dict[str, Any]) -> bool:
        """Determine if a file should be processed based on command arguments.
        
        Args:
            doc: Document information dictionary
            
        Returns:
            True if file should be processed
        """
        # Check if we should only process uncategorized files
        if getattr(self.args, 'un', True) and not getattr(self.args, 'overwrite', False):
            # Only process if file doesn't have metadata or is uncategorized
            meta = doc.get('meta', {})
            return not meta or not meta.get('kategorie')
        
        # Process all files if overwrite is enabled
        return True
    
    def _determine_prompt(self, project: str, bidder: Optional[str]) -> str:
        """Determine the appropriate prompt based on file location.
        
        Args:
            project: Project name
            bidder: Bidder name (None for project documents)
            
        Returns:
            Prompt name to use
        """
        if bidder:
            # Files in B/ directory (bidder documents) use bdok prompt
            return "bdok"
        else:
            # Files in A/ directory (project documents) use adok prompt
            return "adok"
    
    def _generate_metadata(self, content: str, prompt_name: str, identifier: str) -> Optional[Dict[str, Any]]:
        """Generate metadata using AI model.
        
        Args:
            content: Document content
            prompt_name: Name of prompt to use
            identifier: File identifier for logging
            
        Returns:
            Generated metadata dictionary or None if failed
        """
        try:
            # Load prompt
            prompt = self.load_prompt(prompt_name)
            
            self.log(f"Generating metadata using prompt: {prompt_name}", "processing")
            
            # Call AI model to generate metadata
            metadata = self.query_ai_model(
                prompt=prompt,
                input_text=content,
                verbose=self.verbose,
                json_cleanup=True
            )
            
            if metadata:
                self.log(f"Metadata generated successfully for: {identifier}", "success")
                return metadata
            else:
                self.log(f"No metadata generated for: {identifier}", "warning")
                return None
                
        except Exception as e:
            self.log(f"Error generating metadata for {identifier}: {str(e)}", "error")
            return None
    
    def _inject_metadata(self, metadata: Dict[str, Any], project: str, bidder: Optional[str], filename: str) -> None:
        """Inject metadata into the appropriate JSON index file.
        
        Args:
            metadata: Generated metadata
            project: Project name
            bidder: Bidder name (None for project documents)
            filename: Filename
        """
        try:
            # Determine the appropriate JSON file path
            if bidder:
                # For bidder documents, inject into bidder's index file
                json_file_path = self._get_bidder_index_path(project, bidder)
                base_directory = self._get_bidder_directory_path(project, bidder)
            else:
                # For project documents, inject into project's A/ index file
                json_file_path = self._get_project_index_path(project)
                base_directory = self._get_project_directory_path(project)
            
            if not json_file_path or not base_directory:
                self.log(f"Could not determine JSON file path for {filename}", "error")
                return
            
            # Inject metadata using strukt2meta injector
            success = inject_metadata_to_json(
                source_filename=filename,
                metadata=metadata,
                json_file_path=str(json_file_path),
                base_directory=str(base_directory)
            )
            
            if success:
                self.log(f"Metadata injected successfully for: {filename}", "success")
            else:
                self.log(f"Failed to inject metadata for: {filename}", "error")
                
        except Exception as e:
            self.log(f"Error injecting metadata for {filename}: {str(e)}", "error")
    
    def _get_bidder_index_path(self, project: str, bidder: str) -> Optional[Path]:
        """Get the path to bidder's index file.
        
        Args:
            project: Project name
            bidder: Bidder name
            
        Returns:
            Path to bidder's index file or None if not found
        """
        try:
            # Use OFS to find bidder path
            bidder_path = find_bidder_in_project(project, bidder)
            if bidder_path:
                return Path(bidder_path) / ".ofs.index.json"
            return None
        except Exception:
            return None
    
    def _get_project_index_path(self, project: str) -> Optional[Path]:
        """Get the path to project's A/ directory index file.
        
        Args:
            project: Project name
            
        Returns:
            Path to project's A/ index file or None if not found
        """
        try:
            # Use OFS to find project path
            project_path = get_path(project)
            if project_path:
                return Path(project_path) / "A" / ".ofs.index.json"
            return None
        except Exception:
            return None
    
    def _get_bidder_directory_path(self, project: str, bidder: str) -> Optional[Path]:
        """Get the path to bidder's directory.
        
        Args:
            project: Project name
            bidder: Bidder name
            
        Returns:
            Path to bidder's directory or None if not found
        """
        try:
            bidder_path = find_bidder_in_project(project, bidder)
            return Path(bidder_path) if bidder_path else None
        except Exception:
            return None
    
    def _get_project_directory_path(self, project: str) -> Optional[Path]:
        """Get the path to project's A/ directory.
        
        Args:
            project: Project name
            
        Returns:
            Path to project's A/ directory or None if not found
        """
        try:
            project_path = get_path(project)
            if project_path:
                return Path(project_path) / "A"
            return None
        except Exception:
            return None