import mistune
import argparse
import os
import re  # Import regex

# Define the input/output directory
DATA_DIR = "/Users/johannwaldherr/code/ww/ww_private/anonymizer/data"


def chunk_markdown(file_path, chunk_size):
    """Reads a Markdown file and splits it into chunks based on size limit.

    Chunks are created by adding lines until the specified chunk_size is
    approached. A new chunk is started when adding the next line would
    exceed the limit.

    Args:
        file_path (str): The path to the Markdown file.
        chunk_size (int): The target maximum size for each chunk in characters.

    Returns:
        list: A list of dictionaries with 'text' and 'metadata' for each chunk.
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []

    lines = content.splitlines()
    chunks = []
    current_chunk_lines = []
    current_chunk_size = 0  # Represents the character count including potential newlines

    for line in lines:
        line_size = len(line)
        # Calculate the size needed for this line: line_size + 1 (for newline) if chunk is not empty
        # If the current chunk is empty, no newline is added yet.
        size_to_add = line_size + (1 if current_chunk_lines else 0)

        # Check if adding this line would exceed the chunk size
        # and ensure the current chunk isn't empty (to prevent splitting before the first line)
        if current_chunk_lines and (current_chunk_size + size_to_add > chunk_size):
            # Finalize the current chunk
            chunks.append("\n".join(current_chunk_lines))
            # Start a new chunk with the current line
            current_chunk_lines = [line]
            # New chunk starts, size is just the line size (no preceding newline)
            current_chunk_size = line_size
        else:
            # Add the line to the current chunk
            current_chunk_lines.append(line)
            # Update the total size of the current chunk
            current_chunk_size += size_to_add

    # Add the last remaining chunk if it's not empty
    if current_chunk_lines:
        chunks.append("\n".join(current_chunk_lines))

    # Return chunks with metadata including size and position
    return [
        {
            'text': chunk,
            'metadata': {
                'size': len(chunk),
                'position': i+1,
                'total_chunks': len(chunks)
            }
        }
        for i, chunk in enumerate(chunks)
        if chunk.strip()
    ]


def main():
    parser = argparse.ArgumentParser(
        description="Semantic Chunker for Markdown Files")
    # Change argument from full path to base name
    parser.add_argument("filename_base",
                        help="Base name of the Markdown file (e.g., 'ausschreibung' for 'ausschreibung.md')")
    parser.add_argument("-s", "--chunk_size", type=int, default=768,
                        help="Target chunk size in characters (default: 768)")
    args = parser.parse_args()

    # Construct the full input path
    input_filename = f"{args.filename_base}.md"
    input_filepath = os.path.join(DATA_DIR, input_filename)

    print(
        f"Chunking file: {input_filepath} with target size: {args.chunk_size}")
    # Pass the constructed path to the function
    chunks = chunk_markdown(input_filepath, args.chunk_size)

    if chunks:
        # Construct the output path using the base name and directory
        output_filename = f"{args.filename_base}.chunked.md"
        output_filepath = os.path.join(DATA_DIR, output_filename)
        try:
            # Write to the constructed output path
            with open(output_filepath, 'w', encoding='utf-8') as outfile:
                print(
                    f"\n--- Writing {len(chunks)} Chunks to {output_filepath} ---")
                for i, chunk in enumerate(chunks):
                    marker = f"\n--- CHUNK {i+1} (Size: {len(chunk)}) ---\n"
                    outfile.write(marker)
                    outfile.write(chunk)
                    # Optional: print marker to console as well for progress
                    # print(marker.strip())
            print(f"Successfully wrote chunks to {output_filepath}")
        except Exception as e:
            print(f"Error writing to file {output_filepath}: {e}")
    else:
        print("No chunks were generated.")


if __name__ == "__main__":
    main()
