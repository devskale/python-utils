from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
from gliner import GLiNER
from collections import defaultdict
import statistics
import argparse  # Add import for argparse
import json


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
#    print(f"Aggregated entities with median scores and hits (Total hits: {total_hits}):")
    for label in labels:
        #        print(f"{label.capitalize()}:")
        if entities_by_label[label]:
            sorted_entities = sorted(entities_by_label[label].items(
            ), key=lambda x: x[1]['hits'], reverse=True)
            for text, data in sorted_entities:
                count = len(data['scores'])
                median_score = statistics.median(data['scores'])
                hits = data['hits']
#                print(f"   {text}: {count}x, Median Score: {median_score:.4f}, Hits: {hits}")
        else:
            print("   No entities found")
        print()

    return entities_by_label


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
    # Set a really small chunk size, just to show.
    chunk_size=512,
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
    "Produkt",
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
    texts = [Document(page_content=chunk) for chunk in chunks_data['chunks']]
else:
    # Read and chunk markdown file
    with open(args.input_file, 'r') as file:
        mdfile = file.read()
    texts = text_splitter.create_documents([mdfile])
# print the number of texts
print(
    f"Number of texts: {len(texts)} with an aggregate length of {sum(len(text.page_content) for text in texts)} characters.")

# go over first num of chunks and perform entity prediction
# Initialize an empty list to store all entities
max_chunks = 100

entities_all = []

# max_chunks = 1000
for i, text in enumerate(texts):
    if i >= max_chunks:
        break
    entities = model.predict_entities(text.page_content, labels, threshold=0.4)
    if entities:
        # Add chunk number to each entity before extending
        for entity in entities:
            entity['chunk_number'] = i + 1  # 1-based index
        # Append the entities from this chunk to entities_all
        entities_all.extend(entities)
        print(f"Chunk {i + 1} - Found: {len(entities)} : {len(entities_all)}" +
              "." * (i % 8) + " " * (8-(i % 8)), end="\r")

print(f"Done: {len(entities_all)}")
ebyl = aggregate_entities(entities_all, labels)
print_formatted_entities(ebyl)

# Save entities to JSON file
output_path = os.path.splitext(args.input_file)[0] + '.entities.json'
with open(output_path, 'w') as f:
    json.dump(entities_all, f, indent=2)
print(f"Entities saved to: {output_path}")
