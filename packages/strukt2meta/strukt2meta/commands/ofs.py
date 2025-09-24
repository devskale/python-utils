"""OFS command handler for processing files in Opinionated File System structure."""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

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
    raise ImportError(
        "OFS package not found. Please install it with: pip install -e ../ofs")

from .base import BaseCommand
from strukt2meta.injector import inject_metadata_to_json


class OfsCommand(BaseCommand):
    """Handle OFS command for processing files in Opinionated File System structure."""

    # Configurable filename for kriterien output
    KRITERIEN_FILENAME = "projekt.json"

    def __init__(self, args):
        """Initialize OFS command with progress tracking."""
        super().__init__(args)
        self.file_counter = 0
        self.total_files = 0
        self.processed_files = []

    def run(self) -> None:
        """Execute the OFS command for processing files."""
        # Validate kriterien mode parameters
        if self.args.mode == 'kriterien':
            if not self.args.step:
                raise ValueError(
                    "--step parameter is required when using --mode kriterien")
            self.log(
                f"Running in kriterien mode with step: {self.args.step}", "info")

            # Special handling for @all parameter in kriterien mode
            if self.args.ofs == "@all":
                self._run_all_projects_kriterien()
            else:
                self._run_kriterien_mode()
        elif self.args.ofs == "@all":
            self._run_all_projects()
        else:
            self._run_standard_mode()

    def _run_all_projects(self) -> None:
        """Execute OFS processing for all projects."""
        try:
            projects = list_projects()
            if not projects:
                print("No projects found.")
                return

            self.log(f"Found {len(projects)} projects to process", "info")

            for project in projects:
                self.log(f"Starting processing for project: {project}", "info")

                # Reset counters for each project
                self.file_counter = 0
                self.total_files = 0
                self.processed_files = []

                # Count total files for this project
                self._count_total_files(project, None, None)

                # Show total files count
                print(f"📊 {self.total_files} files to process for {project}")

                # Process all files in the project
                self._process_project_files(project)

                # Summary for this project
                print(f"✅ Project {project} complete: {len(self.processed_files)}/{self.total_files} files processed")

        except Exception as e:
            self.log(f"Error processing all projects: {str(e)}", "error")

    def _run_all_projects_kriterien(self) -> None:
        """Execute kriterien processing for all projects."""
        try:
            projects = list_projects()
            if not projects:
                print("No projects found.")
                return

            self.log(f"Found {len(projects)} projects to process in kriterien mode", "info")

            for project in projects:
                self.log(f"Starting kriterien processing for project: {project}", "info")

                # Find AAB document automatically
                aab_filename = self._find_aab_document(project)
                if not aab_filename:
                    print(f"❌ No AAB document found in project: {project}")
                    continue

                print(f"📄 Found AAB document: {aab_filename}")

                # Process the AAB document with kriterien prompt
                success = self._process_kriterien_document(project, aab_filename)

                if success:
                    print(
                        f"✅ Kriterien {self.args.step} processing completed successfully for {project}")
                else:
                    print(f"❌ Kriterien {self.args.step} processing failed for {project}")

        except Exception as e:
            self.log(f"Error processing all projects in kriterien mode: {str(e)}", "error")

    def _run_standard_mode(self) -> None:
        """Execute standard OFS processing mode."""
        # Parse the OFS parameter
        ofs_param = self.args.ofs
        project, bidder, filename = self._parse_ofs_parameter(ofs_param)

        self.log(f"Processing OFS parameter: {ofs_param}", "info")
        self.log(
            f"Parsed - Project: {project}, Bidder: {bidder}, File: {filename}", "info")

        # Count total files first for progress tracking
        self._count_total_files(project, bidder, filename)

        # Show total files count even in non-verbose mode
        print(f"📊 {self.total_files} files to process")

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

        # Summary
        print(
            f"\n✅ Processing complete: {len(self.processed_files)}/{self.total_files} files processed")

    def _run_kriterien_mode(self) -> None:
        """Execute kriterien processing mode."""
        # Parse the OFS parameter - for kriterien mode, we only need project name
        ofs_param = self.args.ofs
        project, _, _ = self._parse_ofs_parameter(ofs_param)

        self.log(f"Processing kriterien for project: {project}", "info")
        self.log(f"Kriterien step: {self.args.step}", "info")

        # Find AAB document automatically
        aab_filename = self._find_aab_document(project)
        if not aab_filename:
            print(f"❌ No AAB document found in project: {project}")
            return

        print(f"📄 Found AAB document: {aab_filename}")

        # Process the AAB document with kriterien prompt
        success = self._process_kriterien_document(project, aab_filename)

        if success:
            print(
                f"✅ Kriterien {self.args.step} processing completed successfully")
        else:
            print(f"❌ Kriterien {self.args.step} processing failed")

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

    def _count_total_files(self, project: str, bidder: Optional[str], filename: str) -> None:
        """Count total files to be processed for progress tracking.

        Args:
            project: Project name
            bidder: Bidder name (optional)
            filename: Filename (optional)
        """
        try:
            if filename:
                # Single file
                self.total_files = 1
            elif bidder:
                # All files for specific bidder
                docs_result = list_bidder_docs_json(project, bidder)
                documents = self._extract_documents_list(docs_result)
                self.total_files = len(
                    [doc for doc in documents if self._should_process_file(doc)])
            else:
                # All files in project
                total = 0

                # Count project documents
                docs_result = list_project_docs_json(project)
                documents = self._extract_documents_list(docs_result)
                total += len([doc for doc in documents if self._should_process_file(doc)])

                # Count bidder documents
                try:
                    bidders = list_bidders(project)
                    for b in bidders:
                        docs_result = list_bidder_docs_json(project, b)
                        documents = self._extract_documents_list(docs_result)
                        total += len([doc for doc in documents if self._should_process_file(doc)])
                except Exception:
                    pass

                self.total_files = total

        except Exception as e:
            self.log(
                f"Warning: Could not count total files: {str(e)}", "warning")
            self.total_files = 0

    def _extract_documents_list(self, docs_result) -> List[Dict[str, Any]]:
        """Extract documents list from various result formats.

        Args:
            docs_result: Result from OFS list functions

        Returns:
            List of document dictionaries
        """
        if isinstance(docs_result, dict) and 'success' in docs_result:
            if docs_result.get('success'):
                return docs_result.get('documents', [])
        elif isinstance(docs_result, dict) and 'documents' in docs_result:
            return docs_result.get('documents', [])
        elif isinstance(docs_result, list):
            return docs_result
        return []

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

        self.file_counter += 1

        # Determine prompt based on file location
        prompt_name = self._determine_prompt(project, bidder)

        try:
            # Read document content using OFS
            doc_result = read_doc(identifier)

            # Check if doc_result is a dict with success/error structure or direct content
            if isinstance(doc_result, dict) and 'success' in doc_result:
                if not doc_result.get('success'):
                    print(
                        f"❌ {self.file_counter}/{self.total_files} {filename} @ {doc_result.get('parser', 'unknown')} @ {prompt_name} (FAIL - read error)")
                    return
                content = doc_result.get('content', '')
                parser = doc_result.get('parser', 'unknown')
            else:
                # Direct content return
                content = doc_result if isinstance(
                    doc_result, str) else str(doc_result)
                parser = 'ofs'

            # Show progress even in non-verbose mode
            print(f"🔄 {self.file_counter}/{self.total_files} {filename} @ {parser}")

            # Generate metadata
            metadata = self._generate_metadata(
                content, prompt_name, identifier)

            # Add Autor field with LLM provenance
            if metadata and isinstance(metadata, dict):
                try:
                    with open("./config.json", "r") as f:
                        config = json.load(f)

                    # Determine provider and model (default task_type)
                    provider = config.get("provider", "tu")
                    model = config.get("model", "mistral-small-3.2-24b")

                    date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                    metadata["Autor"] = f"KI-generiert {provider}@{model}@{prompt_name}@{parser} {date}"
                except Exception as e:
                    self.log(f"Warning: Could not add Autor field: {e}", "warning")

            if metadata:
                # Inject metadata into appropriate JSON file
                success = self._inject_metadata(
                    metadata, project, bidder, filename)
                status = "OK" if success else "FAIL - injection error"
                # Show result with appropriate icon
                icon = "✅" if success else "❌"
                print(
                    f"{icon} {self.file_counter}/{self.total_files} {filename} @ {parser} @ {prompt_name} ({status})")
                if success:
                    self.processed_files.append(filename)
            else:
                print(
                    f"❌ {self.file_counter}/{self.total_files} {filename} @ {parser} @ {prompt_name} (FAIL - no metadata)")

        except Exception as e:
            print(
                f"❌ {self.file_counter}/{self.total_files} {filename} @ unknown @ {prompt_name} (FAIL - {str(e)})")

    def _process_bidder_files(self, project: str, bidder: str) -> None:
        """Process all files for a specific bidder.

        Args:
            project: Project name
            bidder: Bidder name
        """
        self.log(
            f"Processing all files for bidder: {project}@{bidder}", "processing")

        try:
            # Get list of bidder documents
            docs_result = list_bidder_docs_json(project, bidder)
            documents = self._extract_documents_list(docs_result)

            if not documents:
                self.log(f"No documents found for bidder: {bidder}", "warning")
                return

            processable_docs = [
                doc for doc in documents if self._should_process_file(doc)]
            self.log(
                f"Found {len(processable_docs)} processable documents for bidder: {bidder}", "info")

            # Process each document
            for doc in processable_docs:
                filename = doc.get('name')
                if filename:
                    self._process_single_file(project, bidder, filename)

        except Exception as e:
            self.log(
                f"Error processing bidder files for {project}@{bidder}: {str(e)}", "error")

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
            self.log(
                f"Error processing project files for {project}: {str(e)}", "error")

    def _process_project_documents(self, project: str) -> None:
        """Process documents in the project's A/ directory.

        Args:
            project: Project name
        """
        try:
            # Get list of project documents
            docs_result = list_project_docs_json(project)
            documents = self._extract_documents_list(docs_result)

            if not documents:
                self.log(f"No project documents found", "warning")
                return

            processable_docs = [
                doc for doc in documents if self._should_process_file(doc)]
            self.log(
                f"Found {len(processable_docs)} processable project documents", "info")

            # Process each document
            for doc in processable_docs:
                filename = doc.get('name')
                if filename:
                    self._process_single_file(project, None, filename)

        except Exception as e:
            self.log(
                f"Error processing project documents for {project}: {str(e)}", "error")

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

            self.log(
                f"Found {len(bidders)} bidders in project: {project}", "info")

            # Process each bidder's documents
            for bidder in bidders:
                self._process_bidder_files(project, bidder)

        except Exception as e:
            self.log(
                f"Error processing bidder documents for {project}: {str(e)}", "error")

    def _should_process_file(self, doc: Dict[str, Any]) -> bool:
        """Determine if a file should be processed based on command arguments.

        Args:
            doc: Document information dictionary

        Returns:
            True if file should be processed
        """
        filename = doc.get('name', '')

        # Skip markdown variants and metadata files
        # Only process original files (PDFs) and skip generated variants and metadata files
        skip_suffixes = ['.docling.md',
                         '.llamaparse.md', '.marker.md', '.json']
        if any(filename.endswith(suffix) for suffix in skip_suffixes):
            self.log(f"Skipping generated/metadata file: {filename}", "info")
            return False

        # Check if overwrite is enabled - process all remaining files
        if getattr(self.args, 'overwrite', False):
            return True

        # Default behavior: skip files that already have metadata
        # Check both direct kategorie field and nested meta.kategorie field
        kategorie = doc.get('kategorie') or (
            doc.get('meta', {}).get('kategorie') if doc.get('meta') else None)

        if kategorie:
            self.log(
                f"Skipping {filename} - already has metadata (kategorie: {kategorie})", "info")
            return False

        # Process files without metadata
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

    def _generate_metadata(self, content: str, prompt_name: str, identifier: str, task_type: str = "default") -> Optional[Dict[str, Any]]:
        """Generate metadata using AI model.

        Args:
            content: Document content
            prompt_name: Name of prompt to use
            identifier: File identifier for logging
            task_type: Type of task for model configuration ("default", "kriterien")

        Returns:
            Generated metadata dictionary or None if failed
        """
        try:
            # Load prompt
            prompt = self.load_prompt(prompt_name)

            self.log(
                f"Generating metadata using prompt: {prompt_name}", "processing")

            # Call AI model to generate metadata with task-specific configuration
            metadata = self.query_ai_model(
                prompt=prompt,
                input_text=content,
                verbose=self.verbose,
                json_cleanup=True,
                task_type=task_type
            )

            if metadata:
                self.log(
                    f"Metadata generated successfully for: {identifier}", "success")
                return metadata
            else:
                self.log(f"No metadata generated for: {identifier}", "warning")
                return None

        except Exception as e:
            self.log(
                f"Error generating metadata for {identifier}: {str(e)}", "error")
            return None

    def _inject_metadata(self, metadata: Dict[str, Any], project: str, bidder: Optional[str], filename: str) -> bool:
        """Inject metadata into the appropriate JSON index file.

        Args:
            metadata: Generated metadata
            project: Project name
            bidder: Bidder name (None for project documents)
            filename: Filename

        Returns:
            True if injection was successful, False otherwise
        """
        try:
            # Determine the appropriate JSON file path
            if bidder:
                # For bidder documents, inject into bidder's index file
                json_file_path = self._get_bidder_index_path(project, bidder)
                base_directory = self._get_bidder_directory_path(
                    project, bidder)
            else:
                # For project documents, inject into project's A/ index file
                json_file_path = self._get_project_index_path(project)
                base_directory = self._get_project_directory_path(project)

            if not json_file_path or not base_directory:
                return False

            # Inject metadata using strukt2meta injector
            success = inject_metadata_to_json(
                source_filename=filename,
                metadata=metadata,
                json_file_path=str(json_file_path),
                base_directory=str(base_directory)
            )

            return success

        except Exception as e:
            return False

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

    def _find_aab_document(self, project: str) -> Optional[str]:
        """Find AAB document in project using keywords."""
        aab_keywords = ['AAB', 'Ausschreibungsunterlagen',
                        'Ausschreibung', 'Tender']

        try:
            # Get list of project documents
            docs_result = list_project_docs_json(project)
            documents = self._extract_documents_list(docs_result)

            # For kriterien mode, search all documents (not just processable ones)
            # Search for AAB document by keywords
            for doc in documents:
                filename = doc.get('name', '')
                for keyword in aab_keywords:
                    if keyword.lower() in filename.lower():
                        self.log(
                            f"Found AAB document with keyword '{keyword}': {filename}", "info")
                        return filename

            # If no keyword match, look for documents with 'Ausschreibung' category
            for doc in documents:
                kategorie = doc.get('kategorie', '')
                if 'ausschreibung' in kategorie.lower():
                    filename = doc.get('name', '')
                    self.log(
                        f"Found AAB document by category '{kategorie}': {filename}", "info")
                    return filename

            # If still no match, return first document found
            if documents:
                filename = documents[0].get('name', '')
                self.log(f"Using first document as AAB: {filename}", "info")
                return filename

            return None

        except Exception as e:
            self.log(f"Error finding AAB document: {e}", "error")
            return None

    def _process_kriterien_document(self, project: str, filename: str) -> bool:
        """Process AAB document with kriterien prompt and save to projekt.json."""
        try:
            # Determine the prompt name based on step
            # Try different prompt naming conventions
            prompt_candidates = [
                f"kriterien.{self.args.step}",
                f"kriterien.{self.args.step}.3.2"
            ]

            prompt_name = None
            for candidate in prompt_candidates:
                try:
                    # Test if prompt exists by trying to load it
                    self.load_prompt(candidate)
                    prompt_name = candidate
                    break
                except Exception:
                    continue

            if not prompt_name:
                self.log(
                    f"No kriterien prompt found for step: {self.args.step}", "error")
                return False

            # Read the document content
            doc_identifier = f"{project}@A@{filename}"
            doc_result = read_doc(doc_identifier)

            if not doc_result or not doc_result.get('success'):
                self.log(f"Failed to read document: {doc_identifier}", "error")
                return False

            document_content = doc_result.get('content')
            if not document_content:
                self.log(
                    f"No content found in document: {doc_identifier}", "error")
                return False

            # Generate metadata using kriterien prompt with kriterien task type
            metadata = self._generate_metadata(
                document_content, prompt_name, doc_identifier, task_type="kriterien")

            # Add Autor field with LLM provenance for kriterien
            if metadata and isinstance(metadata, dict):
                try:
                    with open("./config.json", "r") as f:
                        config = json.load(f)

                    # Determine provider and model for kriterien
                    kriterien_config = config.get("kriterien", {})
                    provider = kriterien_config.get("provider", "tu")
                    model = kriterien_config.get("model", "glm-4.5-355b")

                    date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                    parser = doc_result.get('parser', 'docling')  # Use parser from doc_result or default
                    metadata["Autor"] = f"KI-generiert {provider}@{model}@{prompt_name}@{parser} {date}"
                except Exception as e:
                    self.log(f"Warning: Could not add Autor field for kriterien: {e}", "warning")

            if not metadata:
                self.log("Failed to generate kriterien metadata", "error")
                return False

            # Save to projekt.json in project root
            success = self._save_kriterien_json(project, metadata)

            if success:
                self.log(
                    f"Kriterien {self.args.step} saved successfully", "info")
                return True
            else:
                self.log(f"Failed to save kriterien {self.args.step}", "error")
                return False

        except Exception as e:
            self.log(f"Error processing kriterien document: {e}", "error")
            return False

    def _save_kriterien_json(self, project: str, metadata: dict) -> bool:
        """Save kriterien metadata to projekt.json in project root."""
        try:
            project_path = get_path(project)
            if not project_path:
                self.log(
                    f"Could not find project path for: {project}", "error")
                return False

            kriterien_path = Path(project_path) / self.KRITERIEN_FILENAME

            # Load existing projekt.json if it exists
            existing_data = {}
            if kriterien_path.exists():
                try:
                    with open(kriterien_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except json.JSONDecodeError:
                    self.log(
                        f"Warning: Existing {self.KRITERIEN_FILENAME} is invalid, creating new file", "warning")
                    existing_data = {}

            # Update with new step data
            existing_data[self.args.step] = metadata

            # Save updated data
            with open(kriterien_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)

            self.log(f"Saved {self.KRITERIEN_FILENAME} to: {kriterien_path}", "info")
            return True

        except Exception as e:
            self.log(f"Error saving {self.KRITERIEN_FILENAME}: {e}", "error")
            return False
