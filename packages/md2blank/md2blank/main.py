"""
CLI entry point for md2blank package.
"""
import argparse
import os
import re
import sys
import json
from pathlib import Path
from .glinerfy import aggregate_entities, print_formatted_entities

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
    parser.add_argument('output', nargs='?', help='Output file')
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

    args = parser.parse_args()

    if args.directory:
        files = find_markdown_files(args.directory, args.match, args.recursive)
        if args.verbose:
            print(f"Found {len(files)} markdown files:")
        print("\n".join(files))
    elif args.input:
        if args.verbose:
            print(f"Processing {args.input} -> {args.output}")

        # Process the file and save chunks to JSON
        import json
        chunks = process_file(args.input, args.chunk_size)
        with open('chunks.temp.json', 'w') as f:
            json.dump(chunks, f, indent=2)

        if args.verbose:
            print(f"Saved {len(chunks)} chunks to chunks.temp.json")

        # Process chunks with GLiNER if requested
        if args.provider == 'gliner':
            from .glinerfy import GLiNER
            model = GLiNER.from_pretrained(args.model, load_tokenizer=True)
            labels = ["City", "Country"]

            entities_all = []
            for chunk in chunks['chunks']:
                entities = model.predict_entities(
                    chunk['text'], labels, threshold=0.6)
                if entities:
                    entities_all.extend(entities)

            ebyl = aggregate_entities(entities_all, labels)

            # Save entities to JSON
            with open('entities.json', 'w') as f:
                json.dump(ebyl, f, indent=2)

            if args.verbose:
                print(f"Saved entities to entities.json")
                print_formatted_entities(ebyl)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
