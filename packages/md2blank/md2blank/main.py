"""
CLI entry point for md2blank package.
"""
import argparse
import os
import re
import sys
import json
from pathlib import Path
# Import the necessary functions from glinerfy
# Make sure predict_entities_from_texts returns (entities, processed_count)
from .glinerfy import aggregate_entities, print_formatted_entities, predict_entities_from_texts
from gliner import GLiNER # Import GLiNER for model loading
from langchain_core.documents import Document # Import Document for text preparation

try:
    from .s1chunk import chunk_markdown
except ImportError as e:
    print(f"Error: Missing required dependency - {e}", file=sys.stderr)
    print("Please install the required packages with: pip install mistune", file=sys.stderr)
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
        "chunks": chunks
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
    parser.add_argument(
        '-m', '--match', help='Pattern to match in markdown files')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output')
    parser.add_argument('-c', '--chunk-size', type=int, default=768,
                        help='Chunk size in characters (default: 768)')
    parser.add_argument('-p', '--provider', choices=['gliner'], default='gliner',
                        help='Entity recognition provider (currently only "gliner" supported)')
    parser.add_argument('--model', default='knowledgator/modern-gliner-bi-large-v1.0',
                        help='Model to use for the specified provider')
    parser.add_argument('--threshold', type=float, default=0.4,
                        help='Confidence threshold for entity recognition (default: 0.4)')
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
        base_filename = os.path.splitext(chunks_info['filename'])[0]
        chunk_key = f"{base_filename}_{args.chunk_size}"
        if chunk_key in output_data["chunks"]:
            if args.verbose:
                print(f"Removing existing chunk data for key: {chunk_key}")
            output_data["chunks"].pop(chunk_key, None)

        # Add new chunk data under "chunks"
        output_data["chunks"][chunk_key] = {
            "filename": chunks_info['filename'],
            "characters": chunks_info['characters'],
            "chunk_size": args.chunk_size,
            "chunk_count": chunks_info['chunk_count'],
            "chunks": chunks_info['chunks']
        }

        # 3. Process chunks with GLiNER if requested
        entities_all = []
        processed_chunk_count = 0
        entity_key = None  # Initialize entity_key
        if args.provider == 'gliner':
            # Define the standard labels
            labels = [
                "Person", "Firma", "Location", "City", "Country", "Date",
                "Money", "Produkt", "Email", "Phone Number", "Address"
            ]

            # Load the GLiNER model
            if args.verbose:
                print(f"Loading GLiNER model: {args.model}")
            model = GLiNER.from_pretrained(args.model, load_tokenizer=True)

            # Prepare texts
            texts = [Document(page_content=chunk.get('text', '')) for chunk in chunks_info.get('chunks', [])]

            if args.verbose:
                print(f"Predicting entities from {len(texts)} text chunks...")

            entities_all, processed_chunk_count = predict_entities_from_texts(
                texts,
                model,
                labels,
                threshold=args.threshold,
                max_chunks=args.max_chunks
            )

            # Determine entity key and remove if exists under "entities"
            sanitized_model_name = args.model.replace('/', '_').replace('\\', '_')
            entity_key = f"{args.provider}_{sanitized_model_name}_{args.chunk_size}"
            if entity_key in output_data["entities"]:
                if args.verbose:
                    print(f"Removing existing entity data for key: {entity_key}")
                output_data["entities"].pop(entity_key, None)

            # Add new entity data under "entities"
            output_data["entities"][entity_key] = {
                "provider": args.provider,
                "model": args.model,
                "threshold": args.threshold,
                "max_chunks_processed": processed_chunk_count,
                "entities": entities_all
            }

            if args.verbose:
                print(f"Predicted {len(entities_all)} entities from {processed_chunk_count} chunks.")

                # Optionally print aggregated entities in verbose mode
                print("\nAggregated Entities Found:")
                ebyl = aggregate_entities(entities_all, labels)
                print_formatted_entities(ebyl)
        elif args.provider:
            print(f"Provider '{args.provider}' not currently supported for entity extraction.", file=sys.stderr)

        # 4. Save the updated, structured output_data to the JSON file
        try:
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"Saved updated data to {output_file}")
            # More detailed print message reflecting the new structure
            print(f"  - Chunk data under key: 'chunks.{chunk_key}'")
            if entity_key:
                print(f"  - Entity data under key: 'entities.{entity_key}' ({len(entities_all)} entities)")
        except Exception as e:
            print(f"Error writing JSON to {output_file}: {e}", file=sys.stderr)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
