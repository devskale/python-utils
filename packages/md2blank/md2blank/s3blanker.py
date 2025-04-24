import os
import re
import sys
from collections import defaultdict


def parse_entities_file(filepath):
    """Parses the .entities.md file and returns a dict mapping chunk headers to entities."""
    entities_by_chunk = defaultdict(list)
    current_chunk_header = None
    in_code_block = False

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                stripped_line = line.strip()
                # Identify chunk headers
                if stripped_line.startswith('--- CHUNK'):
                    # Store entities for the previous chunk before starting a new one
                    if current_chunk_header and entities_by_chunk[current_chunk_header]:
                        # Sort entities by length of value, descending, for safer replacement
                        entities_by_chunk[current_chunk_header].sort(
                            key=lambda x: len(x[1]), reverse=True)
                    current_chunk_header = stripped_line
                    in_code_block = False  # Reset code block status for new chunk
                elif stripped_line == '```text' and current_chunk_header:
                    in_code_block = True
                elif stripped_line == '```':
                    in_code_block = False
                elif in_code_block and ':' in stripped_line and current_chunk_header:
                    # Parse entity type and value within the code block
                    parts = stripped_line.split(':', 1)
                    if len(parts) == 2:
                        entity_type = parts[0].strip()
                        entity_value = parts[1].strip()
                        # Add only if both type and value are non-empty
                        if entity_type and entity_value:
                            entities_by_chunk[current_chunk_header].append(
                                (entity_type, entity_value))

        # Process the last chunk's entities
        if current_chunk_header and entities_by_chunk[current_chunk_header]:
            entities_by_chunk[current_chunk_header].sort(
                key=lambda x: len(x[1]), reverse=True)

    except FileNotFoundError:
        print(f"Error: Entities file not found at {filepath}")
        return None
    except Exception as e:
        print(f"Error reading or parsing entities file {filepath}: {e}")
        return None

    return entities_by_chunk


def blank_entities_in_content(content, entities, hybrid_mode=False):
    """Replaces entity values in content with placeholders [[EntityType]] or [[EntityType // Value]]."""
    modified_content = content
    if not entities:
        return modified_content

    for entity_type, entity_value in entities:
        # Construct placeholder based on hybrid mode
        if hybrid_mode:
            placeholder = f"[[{entity_type} // {entity_value}]]"
        else:
            placeholder = f"[[{entity_type}]]"

        # Use re.escape to handle potential special characters in the entity value
        # Replace all occurrences within the current chunk's content
        try:
            modified_content = re.sub(
                re.escape(entity_value), placeholder, modified_content)
        except re.error as e:
            print(
                f"  Warning: Regex error replacing '{entity_value}' with '{placeholder}': {e}")
            # Optionally skip this replacement or handle differently
            continue  # Skip this entity if regex fails
    return modified_content


def main():
    # --- Direct Argument Parsing using sys.argv ---
    # Initialize default values
    filename_base = None
    hybrid_mode = False

    # Process command-line arguments
    args = sys.argv[1:]

    # Look for -y or --hybrid flag
    if "-y" in args:
        hybrid_mode = True
        args.remove("-y")
    elif "--hybrid" in args:
        hybrid_mode = True
        args.remove("--hybrid")

    # The remaining argument should be filename_base
    if args:
        filename_base = args[0]
    else:
        print("Error: Missing filename base argument")
        print("Usage: python blanker_s3.py [--hybrid] filename_base")
        exit(1)

    print(
        f"Processing {filename_base} with hybrid mode {'enabled' if hybrid_mode else 'disabled'}")

    # --- File Path Definitions ---
    input_dir = "/Users/johannwaldherr/code/ww/ww_private/anonymizer/data"
    chunked_filename = f"{filename_base}.chunked.md"
    entities_filename = f"{filename_base}.entities.md"
    blank_filename = f"{filename_base}.blank.md"

    chunked_filepath = os.path.join(input_dir, chunked_filename)
    entities_filepath = os.path.join(input_dir, entities_filename)
    blank_filepath = os.path.join(input_dir, blank_filename)

    print(f"Reading entities from: {entities_filepath}")
    entities_map = parse_entities_file(entities_filepath)
    if entities_map is None:
        exit(1)
    print(f"Found entity information for {len(entities_map)} chunks.")

    print(f"Reading original content from: {chunked_filepath}")
    try:
        with open(chunked_filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except FileNotFoundError:
        print(f"Error: Chunked input file not found at {chunked_filepath}")
        exit(1)
    except Exception as e:
        print(f"Error reading chunked input file: {e}")
        exit(1)

    # Split original content into chunks (header and content)
    chunk_pattern = r'(--- CHUNK \d+ \(Size: \d+\) ---)'
    parts = re.split(chunk_pattern, original_content)

    print(f"Writing blanked content to: {blank_filepath}")
    if hybrid_mode:
        print("Hybrid mode enabled.")
    try:
        with open(blank_filepath, 'w', encoding='utf-8') as outfile:
            outfile.write(f"<!-- filepath: {blank_filepath} -->\n")
            outfile.write(f"# Blanked content from {chunked_filename}\n\n")

            current_header = None
            processed_chunks = 0
            for part in parts:
                part_strip = part.strip()
                if not part_strip:  # Skip empty parts from split
                    continue

                if re.match(chunk_pattern, part_strip):
                    # This part is a header
                    current_header = part_strip
                    # Write header directly
                    outfile.write(f"{current_header}\n")
                    processed_chunks += 1
                    print(f"Processing chunk: {current_header}")
                elif current_header:
                    # This part is the content following a header
                    chunk_content = part  # Use original part with whitespace
                    entities_for_chunk = entities_map.get(current_header, [])
                    if not entities_for_chunk:
                        print(
                            f"  No entities found for chunk: {current_header}")

                    # Perform blanking, passing the hybrid flag
                    modified_chunk_content = blank_entities_in_content(
                        chunk_content, entities_for_chunk, hybrid_mode)

                    # Write modified content
                    outfile.write(f"{modified_chunk_content}\n")
                    current_header = None  # Reset header until the next one is found
                else:
                    # Handle content before the first chunk header, if any
                    if part_strip and not re.match(chunk_pattern, part_strip):
                        print("Processing content before first chunk header...")
                        # Decide how to handle this - currently writing as is
                        outfile.write(part)

        print(
            f"\nBlanking complete. Processed {processed_chunks} identified chunks.")
        print(f"Results saved to: {blank_filepath}")

    except Exception as e:
        print(f"Error writing blanked output file: {e}")
        exit(1)


if __name__ == "__main__":
    main()
