strukt2meta

takes structured data or images and generates metadata using AI.

## features
- Can work with OFS (opinionated file system).
- Analyzes markdown and converts it into metadata (based on a prompt).
  - Can insert this metadata into JSON of OFS.
- Can work on OFS files, directories, and file trees recursively.
- Retrieves a file path (strukt context).
- Accepts a prompt (e.g., from a template).
- queries an AI model with context (strukt) and the provided prompt.
- Typically returns a JSON response.
- Injects the JSON response into a JSON file.

## architecture
uses credgoo for retrieving APIKEYS, github.com/devskale/python-utils
uses uniinfer to access ai models from provider tu (setup via a config file), github.com/devskale/python-utils
python

## STATUS / TODO
[x] Setup basic package structure
[x] Basic Setup
    [x] install uniinfer, credgoo
    [x] config (provider, model, tokens)
    [x] prompts file
    [x] calling api with uniinfer
    [x] JSON cleanify routine to handle AI-generated JSON
[x] JSON Injection Feature
    [x] Create parameter file schema for injection operations
    [x] Implement JSON file reader/writer with safe backup
    [x] Add filename matching logic for target file identification
    [x] Create metadata injection engine
    [x] Add CLI interface for injection operations
    [x] Add validation for injection schema
    [x] Error handling and rollback mechanisms
[x] Lampen Project Integration
    [x] Create specialized prompt for German lighting documents
    [x] Configure injection parameters for Lampen project
    [x] Implement centralized model configuration
    [x] Test and validate metadata injection for real documents
    [x] Debug and fix prompt-schema alignment issues
    [x] Successful metadata injection into production JSON file

## JSON Injection Analysis

### Current JSON Structure (.pdf2md_index.json)
The target JSON file contains:
- Root object with "files" array and "directories" array
- Each file entry has: name, size, hash, parsers, and optional "meta" object
- Meta object contains fields like "kategorie" and "name"
- Some files have no meta object (need to create it)

### Proposed Parameter File Schema
```json
{
  "input_path": "path/to/source/file.md",
  "prompt": "prompt_name_or_path",
  "ai_model": "model_override_optional", 
  "json_inject_file": "/path/to/.pdf2md_index.json",
  "target_filename": "specific_file.pdf",
  "injection_schema": {
    "meta": {
      "kategorie": "ai_generated_field",
      "name": "ai_generated_field",
      "custom_field": "ai_generated_field"
    }
  }
}
```

### Implementation Strategy
1. Parameter file driven approach for flexibility
2. Safe JSON manipulation with backup/restore
3. Filename matching to find target entry in JSON
4. Schema-driven field injection into meta object
5. AI response parsing and validation
6. Atomic operations with rollback capability

### Key Considerations
- Handle missing meta objects (create if needed)
- Validate AI response matches expected schema
- Backup original JSON before modification
- Support both exact filename match and pattern matching
- Allow partial updates (only specified fields)
- Maintain JSON structure integrity

## Implementation Summary

### Files Created
- `strukt2meta/injector.py` - Core injection engine with JSONInjector class
- `strukt2meta/inject_cli.py` - Standalone CLI for injection operations  
- `prompts/metadata_extraction.md` - Specialized prompt for metadata extraction
- `prompts/lampen_metadata_extraction.md` - German lighting documents prompt
- `injection_params_sample.json` - Sample parameter configuration
- `lampen_injection_params.json` - Lampen project specific configuration
- `sample_document.md` - Test document for demonstration
- `test_injection.py` - Test script for validation
- `test_lampen_injection.py` - Lampen project specific test script
- `debug_metadata.py` - Debug script for metadata generation testing
- `inject_with_debug.py` - Complete injection with debug output
- `inject_single_file.py` - Single file injection script

### Usage Examples

#### Command Line Usage
```bash
# Generate metadata (original functionality)
python -m strukt2meta.main generate --i input.md --p zusammenfassung --o output.json

# Inject metadata into JSON file
python -m strukt2meta.main inject --params injection_params.json --verbose

# Dry run to test configuration
python -m strukt2meta.main inject --params injection_params.json --dry-run
```

#### Programmatic Usage
```python
from strukt2meta.injector import JSONInjector

injector = JSONInjector("injection_params.json")
result = injector.inject()
```

### Key Features Implemented
- Parameter-driven configuration for flexible injection operations
- Safe JSON manipulation with automatic backup creation
- Schema validation for AI-generated metadata
- Rollback capability for error recovery
- Support for both CLI and programmatic interfaces
- Comprehensive error handling and logging

## Lessons Learned

### Technical Insights
- JSON manipulation requires careful handling of file encoding and structure preservation
- AI response validation is crucial for reliable metadata injection
- Backup and rollback mechanisms are essential for production use
- Parameter files provide excellent flexibility for different use cases
- Prompt structure must align exactly with injection schema expectations
- Centralized configuration (config.json) prevents parameter duplication
- Debug scripts are invaluable for troubleshooting injection issues

### Architecture Benefits
- Modular design allows easy extension for different JSON structures
- Schema-driven approach ensures consistent metadata format
- Separation of concerns between generation and injection operations
- Specialized prompts enable domain-specific metadata extraction
- Flexible parameter system supports project-specific configurations

### Production Deployment Success
- Successfully deployed to real Lampen project with 22+ documents
- Metadata injection working reliably with German procurement documents
- Automated backup and validation ensures data integrity
- Schema validation prevents malformed metadata injection

## Lampen Project Case Study

### Project Overview
The Lampen project represents the first production deployment of strukt2meta for extracting metadata from German lighting procurement documents.

### Configuration
- Target JSON: `.pdf2md_index.json` with 22+ document entries
- AI Model: mistral-small-3.1-24b via TU provider
- Language: German document processing
- Schema: kategorie, name, dokumenttyp, thema, sprache

### Key Achievements
- Created specialized German prompt for lighting industry documents
- Implemented centralized model configuration in config.json
- Successfully injected metadata for document "191341-00.pdf"
- Established reliable backup and validation workflow
- Debugged and resolved prompt-schema alignment issues

### Technical Solutions
- Removed ai_model duplication from parameter files
- Updated prompt to provide meta-wrapper structure
- Created comprehensive debug scripts for troubleshooting
- Implemented cache-aware metadata generation
- Validated JSON structure preservation during injection

