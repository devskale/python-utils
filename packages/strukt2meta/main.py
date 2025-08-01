import argparse
import json
import os
from strukt2meta.main import generate_metadata

# Placeholder for AI model interaction
def query_ai_model(prompt, input_text):
    # Simulate AI model response
    return generate_metadata(input_text)

def load_prompt(prompt_name):
    prompts_dir = "./prompts"
    prompt_path = os.path.join(prompts_dir, f"{prompt_name}.md")
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    with open(prompt_path, "r") as prompt_file:
        return prompt_file.read()

def main():
    parser = argparse.ArgumentParser(description="Process a strukt file and generate JSON metadata.")
    parser.add_argument("--i", "--inpath", required=True, help="Path to the input markdown strukt file")
    parser.add_argument("--p", "--prompt", default="zusammenfassung", help="Prompt file name (without .md) to use from the ./prompts directory (default: zusammenfassung)")
    parser.add_argument("--o", "--outfile", required=True, help="Path to the output JSON file")

    args = parser.parse_args()

    # Read the input file
    with open(args.i, "r") as infile:
        input_text = infile.read()

    # Load the prompt
    prompt = load_prompt(args.p)

    # Query the AI model
    result = query_ai_model(prompt, input_text)

    # Write the result to the output file
    with open(args.o, "w") as outfile:
        json.dump(result, outfile, indent=4)

if __name__ == "__main__":
    main()