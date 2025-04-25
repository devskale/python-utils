"""
CLI entry point for md2blank package.
"""
import argparse
import os
import re
import sys
import json
from pathlib import Path
import subprocess
import tempfile  # Ensure tempfile is imported
import time  # Import time for sleep functionality

# Import the necessary functions from glinerfy
# Make sure predict_entities_from_texts returns (entities, processed_count)
from .glinerfy import aggregate_entities, print_formatted_entities, predict_entities_from_texts
from gliner import GLiNER  # Import GLiNER for model loading
from langchain_core.documents import Document  # Import Document for text preparation

# Import unipii for LLM-based entity extraction
try:
    from .unipii import get_entities_from_text
except Exception as e:  # Catch specific exception
    # This variable can be checked later to see if import succeeded
    get_entities_from_text = None
    print(f"Warning: Failed to import '.unipii.get_entities_from_text'. Error: {e}", file=sys.stderr)  # Print the actual error
    print("LLM-based entity extraction via direct import will not be available. Will attempt fallback to subprocess.", file=sys.stderr)

# Import s1chunk
try:
    from .s1chunk import chunk_markdown
except ImportError as e:
    print(f"Error: Missing required dependency - {e}", file=sys.stderr)
    print("Please install the required packages, e.g., with: pip install mistune", file=sys.stderr)
    sys.exit(1)


def find_markdown_files(directory, pattern=None, recursive=False):
    """Find markdown files in directory that match pattern."""
    matches = []
    glob_pattern = "**/*.md" if recursive else "*.md"
    for md_file in Path(directory).glob(glob_pattern):
        if pattern:
            with open(md_file, 'r') as f:
                content = f.read()
                if re.search(pattern, content):
                    matches.append(str(md_file))
        else:
            matches.append(str(md_file))
    return matches


def process_file(input_file, chunk_size=768):
    """Process a markdown file using sophisticated chunking approach."""
    chunks = chunk_markdown(input_file, chunk_size=chunk_size)
    file_info = {
        "filename": os.path.basename(input_file),
        "characters": len(open(input_file, 'r').read()),
        "chunk_count": len(chunks),
        "chunks": chunks,
    }
    return file_info


def main():
    """Process markdown files with optional directory scanning."""
    parser = argparse.ArgumentParser(description='Markdown to Blank Converter')
    parser.add_argument('input', nargs='?', help='Input markdown file')
    parser.add_argument('output', nargs='?', help='Output JSON file for chunks and entities')
    parser.add_argument('-d', '--directory',
                        help='Directory to scan for markdown files')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='Recursively scan directories')
    parser.add_argument('-m', '--match', help='Pattern to match in markdown files')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output')
    parser.add_argument('-c', '--chunk-size', type=int, default=768,
                        help='Chunk size in characters (default: 768)')
    # Remove choices constraint, update help text
    parser.add_argument('-p', '--provider', default='gliner',
                        help='Entity recognition provider (e.g., "gliner", "ollama", "gemini"). Non-"gliner" providers use the unipii LLM extractor.')
    parser.add_argument('--model', default='knowledgator/modern-gliner-bi-large-v1.0',
                        help='Model to use for the specified provider')
    parser.add_argument('--threshold', type=float, default=0.4,
                        help='Confidence threshold for entity recognition (GLiNER only, default: 0.4)')
    parser.add_argument('--max-chunks', type=int, default=1000,
                        help='Maximum number of chunks to process for entity recognition (default: 1000)')
    args = parser.parse_args()

    if args.directory:
        files = find_markdown_files(args.directory, args.match, args.recursive)
        if args.verbose:
            print(f"Found {len(files)} markdown files:")
            print("\n".join(files))
    elif args.input:
        output_file = args.output if args.output else os.path.splitext(args.input)[0] + '.json'
        if args.verbose:
            print(f"Processing {args.input} -> {output_file}")

        # Initialize output data with top-level keys - try loading existing file first
        output_data = {"chunks": {}, "entities": {}}
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r') as f:
                    loaded_data = json.load(f)
                    # Ensure the loaded data has the expected top-level keys
                    if isinstance(loaded_data.get("chunks"), dict):
                        output_data["chunks"] = loaded_data["chunks"]
                    if isinstance(loaded_data.get("entities"), dict):
                        output_data["entities"] = loaded_data["entities"]
                if args.verbose:
                    print(f"Loaded existing data from {output_file}")
            except json.JSONDecodeError:
                print(f"Warning: Could not decode existing JSON from {output_file}. Starting fresh.", file=sys.stderr)
                output_data = {"chunks": {}, "entities": {}}  # Reset on error
            except Exception as e:
                print(f"Warning: Could not read {output_file}: {e}. Starting fresh.", file=sys.stderr)
                output_data = {"chunks": {}, "entities": {}}  # Reset on error

        # 1. Process the file and get chunk information
        chunks_info = process_file(args.input, args.chunk_size)
        if args.verbose:
            print(f"Generated {chunks_info['chunk_count']} chunks.")

        # 2. Determine chunk key and remove if exists under "chunks"
        # This ensures we only update/replace the chunks for the current file and chunk size.
        base_filename = os.path.splitext(chunks_info['filename'])[0]
        chunk_key = f"{base_filename}_{args.chunk_size}"
        if chunk_key in output_data["chunks"]:
            if args.verbose:
                print(f"Removing existing chunk data for key: {chunk_key}")
            output_data["chunks"].pop(chunk_key, None)  # Remove only the specific key

        # Add new chunk data under "chunks"
        if args.verbose:
            print(f"Adding/updating chunk data under key: 'chunks.{chunk_key}'")
        output_data["chunks"][chunk_key] = {
            "filename": chunks_info['filename'],
            "characters": chunks_info['characters'],
            "chunk_size": args.chunk_size,
            "chunk_count": chunks_info['chunk_count'],
            "chunks": chunks_info['chunks'],
        }

        # 3. Process chunks with the selected provider
        entities_all = []
        processed_chunk_count = 0
        entity_key = None  # Initialize entity_key

        if args.provider == 'gliner':
            # Define the standard labels
            labels = [
                "Person", "Unternehmen", "Ort", "Stadt", "Land", "Datum",
                "Geld", "Produkt", "E-Mail", "Telefonnummer", "Adresse"
            ]
            # Load the GLiNER model
            if args.verbose:
                print(f"Loading GLiNER model: {args.model}")
            model = GLiNER.from_pretrained(args.model, load_tokenizer=True)
            if args.verbose:
                print(f"Predicting entities from {len(chunks_info['chunks'])} text chunks...")
            texts = [Document(page_content=chunk.get('text', '')) for chunk in chunks_info.get('chunks', [])]
            entities_all, processed_chunk_count = predict_entities_from_texts(
                texts,
                model,
                labels,
                threshold=args.threshold,
                max_chunks=args.max_chunks
            )

        else:  # Handle all non-gliner providers using unipii (direct import or fallback)
            if get_entities_from_text:  # Check if import was successful
                if args.verbose:
                    print(f"Using imported unipii module with provider: {args.provider}, model: {args.model}")
                processed_chunk_count = 0
                chunk_limit = min(len(chunks_info.get('chunks', [])), args.max_chunks)
                for i, chunk in enumerate(chunks_info.get('chunks', [])[:chunk_limit]):
                    if args.verbose:
                        print(f"Processing chunk {i+1}/{chunk_limit} via unipii import...")
                    chunk_text = chunk.get('text', '')
                    if not chunk_text:
                        continue
                    # Extract entities using imported function
                    chunk_entities = get_entities_from_text({
                        'text': chunk_text,
                        'metadata': {
                            'chunk_number': i + 1,
                            'provider': args.provider,
                            'model': args.model,
                            'source_filename': chunks_info['filename']
                        },
                    })
                    if chunk_entities:
                        if args.verbose:
                            print(f"--- Entitäten von unipii (chunk {i+1}) ---")
                            if isinstance(chunk_entities, list):
                                for entity in chunk_entities:
                                    entity_type = entity.get('label', 'N/A')
                                    entity_value = entity.get('text', 'N/A')
                                    print(f"  - Typ: {entity_type} : {entity_value}")
                            else:
                                print(json.dumps(chunk_entities, indent=2))
                            print("------------------------------------------")
                        entities_all.extend(chunk_entities)
                    processed_chunk_count += 1
                    time.sleep(3)  # <-- Added 3-second pause between LLM calls by unipii.py
 
            else:  # Fallback to external process if import failed
                print("Using external unipii process as fallback...", file=sys.stderr)
                temp_chunked_path = None # Initialize path variable
                entities_path = None
                SUBPROCESS_TIMEOUT = 180  # Timeout in seconds (e.g., 3 minutes)
                try:
                    # Create a temporary file for the chunked content
                    import tempfile
                    # Use delete=False so the file persists after closing for the subprocess
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.chunked.md', delete=False, encoding='utf-8') as temp_file:
                        temp_chunked_path = temp_file.name
                        # Write chunk headers and content to the temp file
                        for i, chunk in enumerate(chunks_info.get('chunks', [])[:args.max_chunks]):
                            temp_file.write(f"--- CHUNK {i + 1} (Size: {len(chunk.get('text', ''))}) ---\n")
                            temp_file.write(chunk.get('text', '') + "\n\n")

                    # Derive expected entities path based on the temporary input path
                    entities_path = temp_chunked_path.replace('.chunked.md', '.entities.md')

                    # Run unipii as external process, passing the FULL paths
                    cmd = [
                        sys.executable,
                        os.path.join(os.path.dirname(__file__), "unipii.py"),
                        temp_chunked_path,  # Pass the full path to the temp file
                        "-p", args.provider,
                        "-m", args.model
                    ]
                    if args.verbose:
                        print(f"Running command: {' '.join(cmd)}")
                        print(f"Timeout set to {SUBPROCESS_TIMEOUT} seconds.")

                    # Execute unipii with timeout
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        timeout=SUBPROCESS_TIMEOUT  # Add timeout
                    )
                    if result.returncode != 0:
                        # Print stderr from the subprocess if it failed
                        print(f"Error running unipii (return code {result.returncode}):\n--- stderr ---\n{result.stderr}\n--- stdout ---\n{result.stdout}\n--------------", file=sys.stderr)
                    else:
                        if args.verbose:
                             print(f"unipii stdout:\n{result.stdout}") # Show stdout in verbose mode
                        # Read the entities from the output file
                        if os.path.exists(entities_path):
                            with open(entities_path, 'r', encoding='utf-8') as f:
                                entity_content = f.read()
                            # --> Update verbose printing for subprocess results <--
                            if args.verbose:
                                print(f"--- Raw entity content from unipii subprocess output file ({entities_path}) ---")
                                try:
                                    parsed_entities = json.loads(entity_content)
                                    if isinstance(parsed_entities, list):
                                        for entity in parsed_entities:
                                            entity_type = entity.get('type', 'N/A')
                                            entity_value = entity.get('value', 'N/A')
                                            print(f"  - Type: {entity_type}")
                                            print(f"    Value: {entity_value}")
                                    else:
                                        # Fallback if not a list
                                        print(json.dumps(parsed_entities, indent=2))
                                except json.JSONDecodeError:
                                    print("  (Could not parse content as JSON)")
                                    print(entity_content) # Print raw content if parsing fails
                                print("-----------------------------------------------------------------------------")
                            # Attempt to parse and add entities if possible
                            try:
                                parsed_entities = json.loads(entity_content)
                                if isinstance(parsed_entities, list):
                                     entities_all.extend(parsed_entities)
                            except json.JSONDecodeError:
                                 print(f"Warning: Could not parse entities from {entities_path}. Entities from this file will be missing.", file=sys.stderr)

                            processed_chunk_count = len(chunks_info.get('chunks', [])[:args.max_chunks])
                        else:
                             print(f"Warning: unipii process succeeded but output file '{entities_path}' not found.", file=sys.stderr)

                except subprocess.TimeoutExpired as e:
                    print(f"Error: unipii subprocess timed out after {SUBPROCESS_TIMEOUT} seconds.", file=sys.stderr)
                    # Optionally print whatever output/error was captured before timeout
                    if e.stdout:
                        print(f"--- stdout before timeout ---\n{e.stdout}\n--------------", file=sys.stderr)
                    if e.stderr:
                        print(f"--- stderr before timeout ---\n{e.stderr}\n--------------", file=sys.stderr)
                    print("Entity extraction failed due to timeout.", file=sys.stderr)
                    entities_all = []
                    processed_chunk_count = 0
                except Exception as e:
                    print(f"Error setting up or running external unipii process: {e}", file=sys.stderr)
                    print("Entity extraction failed. No entities will be included in output.", file=sys.stderr)
                    entities_all = []
                    processed_chunk_count = 0
                finally:
                    # Clean up temp files if they exist
                    if temp_chunked_path and os.path.exists(temp_chunked_path):
                        try:
                            os.remove(temp_chunked_path)
                            if args.verbose: print(f"Removed temp file: {temp_chunked_path}")
                        except OSError as e:
                            print(f"Warning: Could not remove temp file {temp_chunked_path}: {e}", file=sys.stderr)
                    if entities_path and os.path.exists(entities_path):
                         try:
                            os.remove(entities_path)
                            if args.verbose: print(f"Removed temp file: {entities_path}")
                         except OSError as e:
                            print(f"Warning: Could not remove temp file {entities_path}: {e}", file=sys.stderr)

        # Determine entity key using the actual provider name
        sanitized_model_name = args.model.replace('/', '_').replace('\\', '_')
        entity_key = f"{args.provider}_{sanitized_model_name}_{args.chunk_size}"  # Uses the actual provider name

        # Remove existing entity data ONLY for the current provider/model/chunk_size combination.
        # Other entity entries in the JSON will be preserved.
        if entity_key in output_data["entities"]:
            if args.verbose:
                print(f"Removing existing entity data for key: 'entities.{entity_key}'")
            output_data["entities"].pop(entity_key, None)  # Remove only the specific key

        # Add new entity data under "entities" for the specific key
        if args.verbose:
            print(f"Adding/updating entity data under key: 'entities.{entity_key}'")
        
        # Structure the entity data based on the provider
        if args.provider == 'gliner':
            output_data["entities"][entity_key] = {
                "provider": args.provider,
                "model": args.model,
                "threshold": args.threshold,  # Keep threshold for gliner
                "max_chunks_processed": processed_chunk_count,
                "entities": entities_all
            }
        else: # For unipii providers
             output_data["entities"][entity_key] = {
                "provider": args.provider,
                "model": args.model,
                # No threshold for LLM-based extraction
                "max_chunks_processed": processed_chunk_count,
                "entities": entities_all # entities_all already contains the list from unipii
            }
        if args.verbose:
            print(f"\nExtracted {len(entities_all)} entities from {processed_chunk_count} chunks.")

            # Optionally print aggregated/listed entities in verbose mode
            if args.provider == 'gliner':
                labels = [
                    "Person", "Firma", "Ort", "Stadt", "Land", "Datum",
                    "Geld", "Produkt", "Email", "Telefonnummer", "Addresse"
                ]
                ebyl = aggregate_entities(entities_all, labels)
                print("\nAggregated Entities Found:")
                print_formatted_entities(ebyl)
            else:  # Assumes unipii or other LLM providers
                print("\nEntity types found (verbose output only):")
                entity_types = set()
                for entity in entities_all:
                    # Use 'label' key as returned by unipii
                    entity_types.add(entity.get('label', 'Unknown'))
                if not entity_types:
                    print("  (None)")
                else:
                    for entity_type in sorted(entity_types):
                        # Use 'label' key for counting
                        type_count = sum(1 for e in entities_all if e.get('label') == entity_type)
                        print(f"- {entity_type}: {type_count} instances")

        # 4. Save the updated, structured output_data to the JSON file
        # The entire output_data dictionary (with potentially updated chunks
        # and potentially updated entities for the specific key) is saved.
        # Existing entity data for other keys remains untouched.
        try:
            with open(output_file, 'w') as f:
                # output_data now contains entities for the current run regardless of provider
                json.dump(output_data, f, indent=2)
            if args.verbose:
                print(f"\nSaved updated data to {output_file}")
                print(f"  - Chunk data under key: 'chunks.{chunk_key}'")
                # Always mention saved entity data if entities were found
                if entity_key in output_data["entities"]:
                    print(f"  - Entity data under key: 'entities.{entity_key}' ({len(entities_all)} entities)")
        except Exception as e:
            print(f"Error writing JSON to {output_file}: {e}", file=sys.stderr)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
