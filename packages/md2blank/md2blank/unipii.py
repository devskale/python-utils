"""
LLM-based PII extraction module compatible with GLiNER interface.
"""
import re
import os
import argparse
# Use relative import for providers_config
from .providers_config import PROVIDER_CONFIGS
# Import uniinfer components and helpers
from uniinfer import (
    ChatMessage,
    ChatCompletionRequest,
    ProviderFactory
)
from credgoo import get_api_key
from dotenv import load_dotenv
import sys  # Import sys for exit
import time  # Import time module
import json  # Import json for output

# Load environment variables from .env file
# This should run when the module is loaded
dotenv_path = os.path.join(os.getcwd(), '.env')
found_dotenv = load_dotenv(dotenv_path=dotenv_path,
                           verbose=True, override=True)
if not found_dotenv:
    print(
        f"Warning: .env file not found at {dotenv_path}. Relying on existing environment variables.")

# --- Credential Handling ---
# These should also be loaded when the module is loaded
credgoo_encryption_token = os.getenv('CREDGOO_ENCRYPTION_KEY')
credgoo_api_token = os.getenv('CREDGOO_BEARER_TOKEN')

# Define the target entities - expanded list
target_entities = "Personenname, Firmenname, Addresse, Telefonnummer, E-Mail"

# --- Prompts ---
# Keep prompts defined globally
prompt0 = """
Du bist ein intelligentes und hochpräzises(NER) Named Entity Recognizer System. Deine Aufgabe ist es die folgenden Entitätstypen im Text zu identifizieren: {target_entities}.
Diese Identifikation findet im Kontext der Prüfung von Ausschreibungsunterlagen und Angebotsunterlagen statt.
Gib jede gefundene Entität in einer neuen Zeile im Format 'Entitätstyp: Entitätswert' aus. Gib NUR die Entitäten aus, keine zusätzlichen Kommentare, Einleitungen oder den Originaltext. Außer den Entitäten antworte mit nichts.
Ignoriere generische oder allgemeine Begriffe wie 'Unternehmen' oder 'Projekte', 'IT-Dienstleistung'.

Text:
{text_chunk}

Identifizierte Entitäten:
"""

prompt1 = """
Du bist ein intelligentes und hochpräzises (NER) Named Entity Recognition System. Deine Aufgabe ist es, die folgenden Entitätstypen im Text zu identifizieren: {target_entities}.
Diese Identifikation findet im Kontext der Prüfung von Ausschreibungsunterlagen und Angebotsunterlagen statt.

WICHTIG: Gib jede gefundene Entität EXAKT so wieder, wie sie im Originaltext erscheint.

Gib jede gefundene Entität in einer neuen Zeile im Format 'Entitätstyp: Entitätswert' aus. Gib NUR die Entitäten aus, keine zusätzlichen Kommentare, Einleitungen oder den Originaltext. Außer den Entitäten antworte mit nichts.
Ignoriere generische oder allgemeine Begriffe wie 'Unternehmen' oder 'Projekte', 'IT-Dienstleistung'.

Text:
{text_chunk}

Identifizierte Entitäten:
"""

# ... other prompt definitions ...

# --- Uniinfer Provider Initialization (Removed from global scope) ---
# Initialization will now happen inside get_entities_from_text or the main block

# Function to call LLM for entity extraction from a text chunk using Uniinfer
def get_entities_from_text(chunk_data):
    """
    Processes a chunk of text through LLM and returns structured entity data
    in a format similar to GLiNER.
    Expects 'provider' and 'model' keys within chunk_data['metadata'].
    """
    text_chunk = chunk_data.get('text', '') # Keep original text chunk for index finding
    metadata = chunk_data.get('metadata', {})
    provider_name = metadata.get('provider')
    model_name = metadata.get('model')
    source_filename = metadata.get('source_filename') # Expect source filename in metadata
    chunk_number = metadata.get('chunk_number')

    # ... (rest of the provider initialization and credential checks remain the same) ...
    if not provider_name or not model_name:
        print("Error: Provider or model name missing in chunk metadata.", file=sys.stderr)
        return []
        
    if not credgoo_encryption_token or not credgoo_api_token:
        print("Error: CREDGOO credentials not loaded. Cannot initialize provider.", file=sys.stderr)
        return []

    # Initialize provider dynamically based on passed arguments
    try:
        provider_config = PROVIDER_CONFIGS.get(provider_name, {})
        extra_params = provider_config.get('extra_params', {})
        
        # Retrieve API key securely
        api_key = get_api_key(
            service=provider_name, 
            encryption_key=credgoo_encryption_token, 
            bearer_token=credgoo_api_token
        )
        
        # Handle cases where API key might not be needed or found gracefully
        if not api_key and provider_name not in ['ollama']: # Example: ollama might not need a key
             print(f"Warning: API key not found for provider {provider_name}, proceeding without it.", file=sys.stderr)

        uni_provider = ProviderFactory().get_provider(
            name=provider_name,
            api_key=api_key,
            **extra_params
        )

    except KeyError as e:
        print(f"Error (get_entities): Provider '{provider_name}' not found. {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error (get_entities): Initializing provider '{provider_name}'. {e}", file=sys.stderr)
        return []

    # Use a default prompt for now, could be made configurable via metadata
    selected_prompt = prompt1 
    formatted_prompt = selected_prompt.format(text_chunk=text_chunk,
                                              target_entities=target_entities)
    try:
        messages = [ChatMessage(role="user", content=formatted_prompt)]
        request = ChatCompletionRequest(
            messages=messages,
            model=model_name,  # Use the model name passed in metadata
            streaming=True,
        )

        full_response = ""
        stream_start_time = time.time()
        is_verbose = True # Simplified for example; integrate with actual verbose flag if possible

        if is_verbose:
            print(f"unipii.py get_entities (Chunk {chunk_number}): Calling stream_complete for model {model_name}...", file=sys.stderr)

        # Use the dynamically initialized uni_provider
        stream = uni_provider.stream_complete(request)

        if is_verbose:
            print(f"unipii.py get_entities (Chunk {chunk_number}): Stream initiated.", file=sys.stderr)

        for chunk in stream:
            if chunk.message and chunk.message.content:
                content = chunk.message.content
                full_response += content

        stream_end_time = time.time()
        total_chunks = metadata.get('total_chunks', '?')  # Added total chunks from metadata if available
        if is_verbose:
            print(f"unipii.py get_entities (Chunk {chunk_number}/{total_chunks}): Stream finished in {stream_end_time - stream_start_time:.2f} seconds. Full response length: {len(full_response)}", file=sys.stderr)
            print(f"--- Raw LLM Response (Chunk {chunk_number}/{total_chunks}) ---", file=sys.stderr)
            print(full_response, file=sys.stderr)
            print(f"---------------------------------------", file=sys.stderr)

        # Added check for empty LLM response
        if not full_response.strip():
            print(f"Warning (Chunk {chunk_number}): Empty LLM response.", file=sys.stderr)
            return []

        # Parse response into structured format similar to GLiNER
        entities = []
        added_entity_keys = set() # Keep track of added entities (chunk, start, end, label)

        for line in full_response.strip().split('\n'):
            if ':' in line:
                entity_type, entity_value = line.split(':', 1)
                entity_type = entity_type.strip()
                entity_value = entity_value.strip()
                if len(entity_value) < 3:  # Skip too tiny entity values
                    continue
                # Find *all* occurrences of the entity_value in the original text_chunk
                try:
                    # Escape potential regex special characters in the entity value
                    escaped_value = re.escape(entity_value)
                    matches_found = 0
                    for match in re.finditer(escaped_value, text_chunk):
                        start_index = match.start()
                        end_index = match.end()
                        
                        # Create a unique key for this potential entity
                        entity_key = (chunk_number, start_index, end_index, entity_type)

                        # Only add if this exact entity hasn't been added before
                        if entity_key not in added_entity_keys:
                            entities.append({
                                'start': start_index,                   # Start index in chunk
                                'end': end_index,                       # End index in chunk
                                'text': entity_value,                   # Original value from LLM
                                'label': entity_type,                   # Type from LLM
                                'score': None,                          # Placeholder for score
                                'chunk_number': chunk_number,           # Keep chunk number
                                'source_filename': source_filename,     # Keep source filename
                            })
                            added_entity_keys.add(entity_key) # Mark this entity as added
                            matches_found += 1

                    if matches_found == 0 and not any(key[0] == chunk_number and key[3] == entity_type and text_chunk[key[1]:key[2]] == entity_value for key in added_entity_keys):
                         # Log a warning only if no matches were found *and* this entity wasn't already added from a previous identical LLM line
                         print(f"Warning (Chunk {chunk_number}): Could not find any occurrence of entity text '{entity_value}' in chunk.", file=sys.stderr)

                except re.error as re_err:
                     print(f"Warning (Chunk {chunk_number}): Regex error finding '{entity_value}': {re_err}. Indices set to -1.", file=sys.stderr)
                     # Add a single entry with -1 indices as fallback, only if not already added
                     fallback_key = (chunk_number, -1, -1, entity_type)
                     if fallback_key not in added_entity_keys:
                         entities.append({
                             'start': -1, 'end': -1, 'text': entity_value, 'label': entity_type, 
                             'score': None, 'chunk_number': chunk_number, 'source_filename': source_filename
                         })
                         added_entity_keys.add(fallback_key)
                except Exception as find_err:
                     print(f"Warning (Chunk {chunk_number}): Unexpected error finding '{entity_value}': {find_err}. Indices set to -1.", file=sys.stderr)
                     # Add a single entry with -1 indices as fallback, only if not already added
                     fallback_key = (chunk_number, -1, -1, entity_type)
                     if fallback_key not in added_entity_keys:
                         entities.append({
                             'start': -1, 'end': -1, 'text': entity_value, 'label': entity_type, 
                             'score': None, 'chunk_number': chunk_number, 'source_filename': source_filename
                         })
                         added_entity_keys.add(fallback_key)

        return entities

    except Exception as e:
        print(f"Error (get_entities) calling/streaming LLM for chunk {chunk_number}: {e}", file=sys.stderr)
        return []


# --- Main processing logic (for standalone execution) ---
if __name__ == "__main__":
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="Extract entities from a chunked markdown file.")
    # Change filename_base to input_filepath
    parser.add_argument(
        "input_filepath", help="The full path to the input chunked markdown file (e.g., /path/to/ausschreibung.chunked.md)")
    parser.add_argument(
        "-p", "--provider",
        help="LLM provider to use (e.g., 'ollama', 'gemini')",
        default="gemini")
    parser.add_argument(
        "-m", "--model",
        help="Model to use (e.g., 'gemma3:4b', 'gemini-2.0-flash')",
        default="gemini-2.0-flash")
    args = parser.parse_args()
    print(f"unipii.py standalone: Starting with args: {args}", file=sys.stderr) # Log start

    # --- File Path Definitions ---
    # Derive output path from input path
    input_filepath = args.input_filepath
    if not input_filepath.endswith(".chunked.md"):
        print(f"Error: Input filepath '{input_filepath}' does not end with '.chunked.md'", file=sys.stderr)
        sys.exit(1)
    output_filepath = input_filepath.replace(".chunked.md", ".entities.md")
    input_filename = os.path.basename(input_filepath) # Get filename for messages
    print(f"unipii.py standalone: Input: {input_filepath}, Output: {output_filepath}", file=sys.stderr) # Log paths

    # Check credentials needed for standalone execution
    if not credgoo_encryption_token or not credgoo_api_token:
        # Ensure errors go to stderr
        print("Error: CREDGOO_ENCRYPTION_KEY or CREDGOO_BEARER_TOKEN not found in environment variables or .env file.", file=sys.stderr)
        print("Please ensure these variables are set for standalone execution.", file=sys.stderr)
        sys.exit(1)
    print("unipii.py standalone: CREDGOO tokens found.", file=sys.stderr) # Log credential check success

    # Read the input file
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"unipii.py standalone: Successfully read input file.", file=sys.stderr) # Log read success
    except FileNotFoundError:
        # Ensure errors go to stderr
        print(f"Error: Input file not found at {input_filepath}", file=sys.stderr)
        sys.exit(1) # Use sys.exit instead of exit
    except Exception as e:
        # Ensure errors go to stderr
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1) # Use sys.exit

    # Split content into chunks using regex (captures header and content separately)
    # Pattern looks for '--- CHUNK X (Size: Y) ---' and captures it, splitting the text
    chunk_pattern = r'(--- CHUNK \d+ \(Size: \d+\) ---)'
    parts = re.split(chunk_pattern, content)
    # Filter out empty strings and combine headers with their content
    chunks = []
    header = None
    chunk_counter = 0
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if re.match(chunk_pattern, part):
            header = part
            # Extract chunk number from header if possible
            match = re.search(r'CHUNK (\d+)', header)
            chunk_counter = int(match.group(1)) if match else chunk_counter + 1
        elif header:
            chunks.append({
                "header": header, 
                "content": part, 
                "number": chunk_counter # Store chunk number
            })
            header = None  # Reset header

    print(f"unipii.py standalone: Split input into {len(chunks)} chunks.", file=sys.stderr) # Log chunk split

    # Open the output file in write mode (to clear previous content)
    try:
        with open(output_filepath, 'w', encoding='utf-8') as outfile:
            # Add filepath comment for consistency with user request format
            outfile.write(f"<!-- filepath: {output_filepath} -->\n")
            # Update header to reflect the dynamic input filename
            outfile.write(f"# Entities extracted from {input_filename} using {args.provider}/{args.model}\n\n")
        print(f"unipii.py standalone: Initialized output file.", file=sys.stderr) # Log output init
    except Exception as e:
        # Ensure errors go to stderr
        print(f"Error creating output file: {e}", file=sys.stderr)
        sys.exit(1) # Use sys.exit

    # Process each chunk and collect entities
    all_entities = []
    processed_count = 0
    print(f"unipii.py standalone: Starting chunk processing loop...", file=sys.stderr) # Log loop start
    for i, chunk_info in enumerate(chunks):
        chunk_header = chunk_info["header"]
        chunk_content = chunk_info["content"]
        chunk_num = chunk_info["number"]

        # Print progress to stderr
        print(f"unipii.py standalone: Processing chunk {chunk_num}/{len(chunks)}...", file=sys.stderr)

        if not chunk_content:
            print(f"unipii.py standalone:   Skipping empty chunk {chunk_num}.", file=sys.stderr)
            continue

        # Prepare chunk_data for the function call
        current_chunk_data = {
            'text': chunk_content,
            'metadata': {
                'chunk_header': chunk_header,
                'chunk_number': chunk_num,
                'provider': args.provider,
                'model': args.model,
                'source_filename': input_filename, # Use derived input_filename
                'total_chunks': len(chunks) # Add total chunks to metadata
            }
        }

        # Get structured entities from chunk using the refactored function
        print(f"unipii.py standalone:   Calling get_entities_from_text for chunk {chunk_num}...", file=sys.stderr) # Log function call
        start_time = time.time()
        entities = get_entities_from_text(current_chunk_data)
        end_time = time.time()
        print(f"unipii.py standalone:   get_entities_from_text for chunk {chunk_num} finished in {end_time - start_time:.2f} seconds.", file=sys.stderr) # Log function return

        if entities:
            all_entities.extend(entities)
            print(f"unipii.py standalone:   Found {len(entities)} entities in chunk {chunk_num}.", file=sys.stderr)
        else:
            print(f"unipii.py standalone:   No entities found or error processing chunk {chunk_num}.", file=sys.stderr)

        processed_count += 1

    print(f"unipii.py standalone: Finished chunk processing loop.", file=sys.stderr) # Log loop end

    # Write all entities to output file in structured format
    try:
        print(f"unipii.py standalone: Writing {len(all_entities)} entities to output file...", file=sys.stderr) # Log write start
        with open(output_filepath, 'w', encoding='utf-8') as outfile: # Use write mode to overwrite
             # Write the list of entities directly as a JSON array
             json.dump(all_entities, outfile, indent=2, ensure_ascii=False) # Use json.dump

        print(f"unipii.py standalone: Successfully wrote entities as JSON.", file=sys.stderr) # Log write success
    except Exception as e:
        print(f"Error writing JSON to output file: {e}", file=sys.stderr)

    print(f"\nunipii.py standalone: Entity extraction complete. Processed {processed_count}/{len(chunks)} chunks.", file=sys.stderr) # Log completion
    print(f"unipii.py standalone: Results saved to: {output_filepath}", file=sys.stderr) # Log final output path
