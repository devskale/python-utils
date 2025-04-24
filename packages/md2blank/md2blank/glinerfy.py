from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
from gliner import GLiNER
from collections import defaultdict
import statistics
import argparse
import json
from langchain_core.documents import Document  # Ensure Document is imported


def aggregate_entities(entities, labels):
    # Create a dictionary to store entities, their scores, and hit counts by label
    entities_by_label = {label: defaultdict(
        lambda: {'scores': [], 'hits': 0}) for label in labels}
    total_hits = 0

    # Process entities
    for entity in entities:
        label = entity['label']
        text = entity['text']
        score = entity['score']
        if label in labels:
            entities_by_label[label][text]['scores'].append(score)
            entities_by_label[label][text]['hits'] += 1
            total_hits += 1

    # Calculate statistics and print results
    for label in labels:
        if entities_by_label[label]:
            sorted_entities = sorted(entities_by_label[label].items(
            ), key=lambda x: x[1]['hits'], reverse=True)
            for text, data in sorted_entities:
                count = len(data['scores'])
                median_score = statistics.median(data['scores'])
                hits = data['hits']
        else:
            print("   No entities found")
        print()

    return entities_by_label


def process_gliner_entities(chunks, model_name, labels, threshold=0.4):
    """Process chunks with GLiNER and return aggregated entities."""
    model = GLiNER.from_pretrained(model_name, load_tokenizer=True)

    entities_all = []
    for chunk in chunks:
        entities = model.predict_entities(
            chunk['text'], labels, threshold=threshold)
        if entities:
            entities_all.extend(entities)

    return aggregate_entities(entities_all, labels)


def print_formatted_entities(ebyl):
    for label, entities in ebyl.items():
        print(f"{label.capitalize()}")

        # Sort entities by mean score in descending order
        sorted_entities = sorted(
            entities.items(),
            key=lambda x: statistics.mean(x[1]['scores']),
            reverse=True
        )

        for entity, data in sorted_entities:
            mean_score = statistics.mean(data['scores'])
            hits = data['hits']
            print(f"   {entity}, {mean_score:.2f}, x{hits}")

        print()  # Empty line between labels


def predict_entities_from_texts(texts, model, labels, threshold=0.4, max_chunks=1000):
    """Predicts entities from a list of text documents using a GLiNER model."""
    entities_all = []
    num_texts = len(texts)
    processed_chunk_count = 0  # Initialize counter
    for i, text in enumerate(texts):
        if i >= max_chunks:
            print(f"\nReached max_chunks limit ({max_chunks}). Stopping processing.")
            break
        processed_chunk_count += 1  # Increment for each processed chunk
        entities = model.predict_entities(text.page_content, labels, threshold=threshold)
        if entities:
            # Add chunk number to each entity before extending
            for entity in entities:
                entity['chunk_number'] = i + 1  # 1-based index
            # Append the entities from this chunk to entities_all
            entities_all.extend(entities)
            print(f"Chunk {i + 1}/{num_texts} - Found: {len(entities)} : Total: {len(entities_all)}" +
                  "." * (i % 8) + " " * (8-(i % 8)), end="\r")
    print(f"\nDone processing {processed_chunk_count} chunks. Total entities found: {len(entities_all)}")
    # Return both the list of entities and the count of processed chunks
    return entities_all, processed_chunk_count


# --- Main execution block ---
if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Process a markdown file for entity recognition.")
    parser.add_argument(
        "input_file", help="The input file to process (either .md or chunks.temp.json)")
    parser.add_argument(
        "-p", "--provider", choices=['gliner'], default='gliner',
        help="Entity recognition provider (currently only 'gliner' supported)")
    parser.add_argument(
        "-m", "--model", default='knowledgator/modern-gliner-bi-large-v1.0',
        help="Model to use for the specified provider")
    parser.add_argument(
        "-c", "--chunk_size", type=int, default=512,
        help="Chunk size for text splitting")
    args = parser.parse_args()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=args.chunk_size,  # Use args.chunk_size
        chunk_overlap=10,
        length_function=len,
        is_separator_regex=False,
    )

    # Initialize model based on provider
    if args.provider == 'gliner':
        model = GLiNER.from_pretrained(args.model, load_tokenizer=True)
    else:
        raise ValueError(f"Unsupported provider: {args.provider}")
    labels = [
        "Person",
        "Firma",
        "Location",
        "City",
        "Country",
        "Date",
        "Money",
        "Product",
        "Email",
        "Phone Number",
        "Address"
    ]

    # Process input file
    print(f"Processing file: {args.input_file}")

    if args.input_file.endswith('.json'):
        # Load chunks from JSON file
        with open(args.input_file, 'r') as f:
            chunks_data = json.load(f)
        # Assuming chunks_data['chunks'] is a list of dicts with 'text'
        texts = [Document(page_content=chunk.get('text', '')) for chunk in chunks_data.get('chunks', [])]
    else:
        # Read and chunk markdown file
        with open(args.input_file, 'r') as file:
            mdfile = file.read()
        texts = text_splitter.create_documents([mdfile])
    # print the number of texts
    print(
        f"Number of texts: {len(texts)} with an aggregate length of {sum(len(text.page_content) for text in texts)} characters.")

    # Use the updated function to predict entities
    max_chunks_to_process = 1000
    # Capture both return values
    entities_all, processed_count = predict_entities_from_texts(
        texts, model, labels, threshold=0.4, max_chunks=max_chunks_to_process
    )

    # Aggregate and print entities
    ebyl = aggregate_entities(entities_all, labels)
    print("\nAggregated Entities (from direct script run):")
    print_formatted_entities(ebyl)

    # Save the raw entities list to JSON file
    output_path = os.path.splitext(args.input_file)[0] + '.entities.json'
    output_struct = {
        "entities": entities_all,
        "processed_chunk_count": processed_count,
        "model": args.model,
        "provider": args.provider
    }
    with open(output_path, 'w') as f:
        json.dump(output_struct, f, indent=2)  # Save structured output
    print(f"Raw entities and info saved to: {output_path}")
